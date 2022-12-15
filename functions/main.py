from google.cloud import firestore
from .preprocess import Preprocessor

client = firestore.Client()

def onNewSample(data, context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)

    sample_id = data["value"]["fields"]["sample_id"]["integerValue"]
    username = data["value"]["fields"]["username"]["stringValue"]
    ppg = data["value"]["fields"]["ppg"]["arrayValue"]
    
    result = Preprocessor(
        ppg=ppg,
        fs=125,
    ).run()
    result['sample_id'] = sample_id
    result['username'] = username
    client.collection('processed_samples').add(result)
    affected_doc.update({
        u'processed': True,
    })

def onValidSample(data, context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])

    affected_doc = client.collection(collection_path).document(document_path)

    cur_value = data["value"]["fields"]["original"]["stringValue"]
    new_value = cur_value.upper() 