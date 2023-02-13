from google.cloud import firestore
from gcp_utils.tools.preprocess import validate_window
from gcp_utils.tools.predict import predict_bp
from gcp_utils.data import config

client = firestore.Client()

CONFIG = config()

# Validate window
def onNewSample(data, context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)
    ppg_raw = [float(x['doubleValue']) for x in data["value"]["fields"]["ppg_raw"]["arrayValue"]['values']]

    result = validate_window(
        ppg=ppg_raw,
        config=CONFIG,
    )
    affected_doc.update({
        u'status': result['status'],
        u'ppg': result['ppg'],
        u'vpg': result['vpg'],
        u'apg': result['apg'],
        u'ppg_scaled': result['ppg_scaled'],
        u'vpg_scaled': result['vpg_scaled'],
        u'apg_scaled': result['apg_scaled'],
    })

# Make prediction on ppg using enceladus (vital-bee-206-serving)
def onValidSample(data, context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)

    status = str(data["value"]["fields"]["status"]["stringValue"])
    if status == 'valid':
        result = predict_bp(data, CONFIG)
        affected_doc.update({
            u'status': result['status'],
            u'abp_scaled': result['abp_scaled'],
            u'abp': result['abp'],
        })
