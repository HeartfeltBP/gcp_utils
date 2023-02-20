from google.cloud import firestore
from gcp_utils import constants
from gcp_utils.tools.preprocess import validate_window
from gcp_utils.tools.predict import predict_bp
from gcp_utils.tools.utils import get_document_context, resample_frame, split_frame, generate_sample_document

client = firestore.Client()

# Split incoming frames (frames collection)
def onNewFrame(data, context):
    collection_path, document_path = get_document_context(context)

    affected_doc = client.collection(collection_path).document(document_path)
    frame = [float(x['doubleValue']) for x in data["value"]["fields"]["frame"]["arrayValue"]['values']]
    fid = str(data["value"]["fields"]["fid"]["stringValue"])
    target = str(data["value"]["fields"]["target"]["stringValue"])

    frame_resamp, n_windows = resample_frame(sig=frame, fs_old=200, fs_new=125, t=2.048)
    samples = split_frame(sig=frame_resamp, n=n_windows)
    processed_frame = [s for s in generate_sample_document(samples, fid)]

    col = client.collection(target).document(document_path.split('/')[0]).collection(u'samples')
    for s in processed_frame:
        col.add(s)

    affected_doc.update({
        u'status': 'processed'
    })

# Validate window
def onNewSample(data, context):
    collection_path, document_path = get_document_context(context)

    affected_doc = client.collection(collection_path).document(document_path)
    ppg_raw = [float(x['doubleValue']) for x in data["value"]["fields"]["ppg_raw"]["arrayValue"]['values']]

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
        u'hr': result['hr'],
        u'snr': result['snr'],
        u'beat_sim': result['beat_sim'],
    })

# Make prediction on ppg using enceladus (vital-bee-206-serving)
def onValidSample(data, context):
    collection_path, document_path = get_document_context(context)

    affected_doc = client.collection(collection_path).document(document_path)

    status = str(data["value"]["fields"]["status"]["stringValue"])
    if status == 'valid':
        result = predict_bp(data, constants.CONFIG)
        affected_doc.update({
            u'status': result['status'],
            u'abp_scaled': result['abp_scaled'],
            u'abp': result['abp'],
        })
