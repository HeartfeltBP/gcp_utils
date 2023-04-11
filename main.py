from google.cloud import firestore
from gcp_utils.tools.preprocess import validate_window, process_frame
from gcp_utils.tools.predict import predict_bp, predict_cardiac_metrics
from gcp_utils.tools.utils import get_document_context, get_json_field, query_collection, generate_window_document, format_as_json
from gcp_utils.constants import CONFIG_PATH, BATCH_SIZE
from database_tools.tools.dataset import ConfigMapper

client = firestore.Client()
cm = ConfigMapper(CONFIG_PATH)

def onUpdateFrame(data, context):
    """Filter and split new frames written to 'bpm_data/{uid}/frames/{fid}'."""
    collection_path, document_name = get_document_context(context)
    doc_reference = client.collection(collection_path).document(document_name)

    status = get_json_field(data, 'status', 'str')
    if status == 'new':
        red_frame = get_json_field(data, 'red_frame', 'list')
        ir_frame = get_json_field(data, 'ir_frame', 'list')
        fid = get_json_field(data, 'fid', 'str')

        processed = process_frame(red_frame, ir_frame, cm=cm)
        cardiac_metrics = predict_cardiac_metrics(
            red=red_frame,
            ir=ir_frame,
            cm=cm,
        )
        doc_reference.update({
            u'status': 'processed',
            u'red_frame_for_presentation': processed['red_frame_for_presentation'],
            u'ir_frame_for_presentation': processed['ir_frame_for_presentation'],
            u'frame_for_prediction': processed['frame_for_prediction'],
            u'pulse_rate': cardiac_metrics['pulse_rate'],
            u'spo2': cardiac_metrics['spo2'],
            u'r': cardiac_metrics['r'],
        })

        windows = [s for s in generate_window_document(processed['windows'], fid)]
        user_reference = '/'.join(collection_path.split('/')[0:-1])
        col = client.collection(user_reference + '/windows')
        for w in windows:
            col.add(w)
    return

def onCreateWindow(data, context):
    """Validate new windows."""
    collection_path, document_name = get_document_context(context)
    doc_reference = client.collection(collection_path).document(document_name)

    ppg = get_json_field(data, 'ppg', 'list')
    result = validate_window(
        ppg=ppg,
        cm=cm,
        force_valid=True,
    )
    doc_reference.update({
        u'status': result['status'],
        u'vpg': result['vpg'],
        u'apg': result['apg'],
        u'ppg_scaled': result['ppg_scaled'],
        u'vpg_scaled': result['vpg_scaled'],
        u'apg_scaled': result['apg_scaled'],
        u'f0': result['f0'],
        u'snr': result['snr'],
        u'beat_sim': result['beat_sim'],
        u'notches': result['notches'],
        u'flat_lines': result['flat_lines'],
    })
    return

def onUpdateWindow(data, context):
    collection_path, document_name = get_document_context(context)
    col_reference = client.collection(collection_path)

    windows = query_collection(col_reference, 'status', '==', 'valid')

    if len(windows) >= BATCH_SIZE:
        windows_paths = [w.reference.path for w in windows]
        result = predict_bp(format_as_json([w.to_dict() for w in windows]), cm)
        for path, abp in zip(windows_paths, result):
            doc_reference = client.document(path)
            doc_reference.update({
                u'status': 'predicted',
                u'abp': abp,
            })

# TODO: Implement logic to only predict on valid windows.
# TODO: Fix frame preprocessing
# TODO: Implement abp postprocessing