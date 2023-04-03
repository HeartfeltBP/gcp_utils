from google.cloud import firestore
from gcp_utils import constants
from gcp_utils.tools.preprocess import validate_window
from gcp_utils.tools.predict import predict_bp
from gcp_utils.tools.utils import get_document_context, resample_frame, split_frame, generate_sample_document
from gcp_utils.constants import CONFIG

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
    frame = [float(x['doubleValue']) for x in data["value"]["fields"]["frame"]["arrayValue"]['values']]

    # Frame ID (uid)
    fid = str(data["value"]["fields"]["fid"]["stringValue"])

    # Target Firestore collection (bpm_data or bpm_data_test)
    target = str(data["value"]["fields"]["target"]["stringValue"])

    # Processing steps
    frame_resamp = resample_frame(sig=frame, fs_old=200, fs_new=125)
    samples = split_frame(sig=frame_resamp, n=int(len(frame_resamp) / CONFIG['win_len']))
    processed_frame = [s for s in generate_sample_document(samples, fid)]

    col = client.collection(target).document(document_path.split('/')[0]).collection(u'windows')
    for s in processed_frame:
        col.add(s)

    affected_doc.update({
        u'status': 'processed'
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

def onValidSample(data, context):
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
