from google.cloud import firestore
from gcp_utils import constants
from gcp_utils.tools.preprocess import validate_window, process_frame
from gcp_utils.tools.predict import predict_bp, predict_cardiac_metrics
from gcp_utils.tools.utils import get_document_context, generate_window_document
from gcp_utils.constants import CONFIG

client = firestore.Client()

def onUpdateFrame(data, context):
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

    has_red = (data["value"]["fields"]["red_frame"]["arrayValue"]["values"] != [])
    has_ir = (data["value"]["fields"]["ir_frame"]["arrayValue"]["values"] != [])
    status = data["value"]["fields"]["status"]["stringValue"]
    if has_red & has_ir & (status == 'new'):
        # New long form frame from BPM device
        red_frame = [float(x['doubleValue']) for x in data["value"]["fields"]["red_frame"]["arrayValue"]["values"]]
        ir_frame = [float(x['doubleValue']) for x in data["value"]["fields"]["ir_frame"]["arrayValue"]["values"]]

        # Frame ID (uid)
        fid = str(data["value"]["fields"]["fid"]["stringValue"])

        # Target Firestore collection (bpm_data or bpm_data_test)
        target = str(data["value"]["fields"]["target"]["stringValue"])

        # Processing steps
        processed = process_frame(red_frame, ir_frame, config=CONFIG)
        cardiac_metrics = predict_cardiac_metrics(
            red=processed['red_frame_for_processing'],
            ir=processed['ir_frame_for_processing'],
            fs=CONFIG['bpm_fs'],
        )
        windows = [s for s in generate_window_document(processed['windows'], fid)]

        col = client.collection(target).document(document_path.split('/')[0]).collection(u'windows')
        for w in windows:
            col.add(w)

        affected_doc.update({
            u'status': 'processed',
            u'red_frame_for_presentation': processed['red_frame_for_presentation'],
            u'ir_frame_for_presentation': processed['ir_frame_for_presentation'],
            u'combined_frame_for_presentation': processed['combined_frame_for_presentation'],
            u'pulse_rate': cardiac_metrics['pulse_rate'],
            u'spo2': cardiac_metrics['spo2'],
            u'r': cardiac_metrics['r'],
        })

def onCreateWindow(data, context):
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

def onUpdateWindow(data, context):
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
