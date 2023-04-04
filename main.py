from google.cloud import firestore
from gcp_utils import constants
from gcp_utils.tools.preprocess import validate_window, flip_and_combine
from gcp_utils.tools.predict import predict_bp, predict_cardiac_values
from gcp_utils.tools.utils import get_document_context, resample_frame, split_frame, generate_window_document
from gcp_utils.constants import CONFIG
from database_tools.preprocessing.functions import bandpass

client = firestore.Client()

def onNewFrame(data, context):
    """Filter and split new frames written to '{uid}/frames'.

    Preprocessing Steps
    -------------------
    1. Apply bandpass filter to frame.
    2. Resample frame.
    4. Calculate SpO2 and pulse rate from frame.
    3. Generate individual windows from frame (for bp pred).
    """
    collection_path, document_path = get_document_context(context)
    affected_doc = client.collection(collection_path).document(document_path)

    # New long form frame from BPM device
    red_frame = [float(x['doubleValue']) for x in data["value"]["fields"]["red_frame"]["arrayValue"]['values']]
    ir_frame = [float(x['doubleValue']) for x in data["value"]["fields"]["ir_frame"]["arrayValue"]['values']]

    # Frame ID (uid)
    fid = str(data["value"]["fields"]["fid"]["stringValue"])

    # Target Firestore collection (bpm_data or bpm_data_test)
    target = str(data["value"]["fields"]["target"]["stringValue"])

    # Processing steps
    red_frame_filt = bandpass(red_frame, low=CONFIG['freq_band'][0], high=CONFIG['freq_band'][1], fs=CONFIG['bpm_fs']).tolist()
    ir_frame_filt = bandpass(ir_frame, low=CONFIG['freq_band'][0], high=CONFIG['freq_band'][1], fs=CONFIG['bpm_fs']).tolist()
    frame_filt = [red_frame_filt, ir_frame_filt]

    pulse_rate, spo2, r = predict_cardiac_values(frame_filt, fs=CONFIG['bpm_fs'])

    flipped_combined = flip_and_combine(frame_filt)
    frame_resamp = resample_frame(sig=flipped_combined, fs_old=CONFIG['bpm_fs'], fs_new=CONFIG['fs'])
    samples = split_frame(sig=frame_resamp, n=int(len(frame_resamp) / CONFIG['win_len']))
    processed_frame = [s for s in generate_window_document(samples, fid)]

    col = client.collection(target).document(document_path.split('/')[0]).collection(u'windows')
    for s in processed_frame:
        col.add(s)

    affected_doc.update({
        u'status': 'processed',
        u'pulse_rate': int(pulse_rate),
        u'spo2': float(spo2),
        u'r': float(r),
    })

def onNewWindow(data, context):
    """Validate new windows."""
    collection_path, document_path = get_document_context(context)
    affected_doc = client.collection(collection_path).document(document_path)

    # Raw ppg window
    ppg_raw = [float(x['doubleValue']) for x in data["value"]["fields"]["ppg_raw"]["arrayValue"]['values']]

    # Perform validation on window and return results
    result = validate_window(
        ppg=ppg_raw,
        config=constants.CONFIG,
    )

    affected_doc.update({
        u'status': result['status'],
        u'ppg': result['ppg'],
        u'vpg': result['vpg'],
        u'apg': result['apg'],
        u'ppg_scaled': result['ppg_scaled'],
        u'vpg_scaled': result['vpg_scaled'],
        u'apg_scaled': result['apg_scaled'],
        u'f0': result['f0'],
        u'snr': result['snr'],
        u'beat_sim': result['beat_sim'],
    })

def onValidWindow(data, context):
    """Make BP prediction using model endpoint (vital-bee-206-serving)."""
    collection_path, document_path = get_document_context(context)
    affected_doc = client.collection(collection_path).document(document_path)

    # Make prediction only if window is valid
    status = str(data["value"]["fields"]["status"]["stringValue"])
    if status == 'valid':
        result = predict_bp(data, constants.CONFIG)
        affected_doc.update({
            u'status': result['status'],
            u'abp_scaled': result['abp_scaled'],
            u'abp': result['abp'],
        })
