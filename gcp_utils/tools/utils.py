import mock
import json
import hashlib
from google.cloud.firestore import CollectionReference, DocumentReference

def get_document_context(context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = '/'.join(path_parts[0:-1])
    document_name = path_parts[-1]
    return (collection_path, document_name)

def get_json_field(data, field, dtype):
    field = data['value']['fields'][field]
    if dtype == 'int':
        value = int(field['integerValue'])
    elif dtype == 'bool':
        value = bool(field['booleanValue'])
    elif dtype == 'str':
        value = str(field['stringValue'])
    elif dtype == 'float':
        value = float(field['floatValue'])
    elif dtype == 'list':
        value = [float(x['doubleValue']) for x in field['arrayValue']['values']]
    else:
        raise ValueError(f'Type \'{dtype}\' is not a supported type')
    return value

def format_as_json(doc) -> dict:
    if isinstance(doc, list):
        n_docs = doc
    elif isinstance(doc, dict):
        n_docs = [doc]
    else:
        n_docs = [x.to_dict() for x in doc]
    data = [{'value': {'fields':
        {key: _default_to_json(value) for key, value in doc.items()}
    }} for doc in n_docs]
    return data

def _default_to_json(x):
    if isinstance(x, int):
        data = {'integerValue': x}
        return data
    elif isinstance(x, str):
        data = {'stringValue': x}
        return data
    elif isinstance(x, bool):
        data = {'booleanValue': x}
        return data
    elif isinstance(x, list):
        data = {'arrayValue': {'values': [{'doubleValue': xx} for xx in x]}}
        return data
    elif isinstance(x, float):
        data = {'floatValue': x}
        return data
    else:
        raise TypeError(f'Type \'{type(x)}\' is not a supported type')

def query_collection(col: CollectionReference, field, condition, value) -> DocumentReference:
    doc_gen = col.where(field, condition, value).stream()
    docs = [d for d in doc_gen]
    return docs

def mock_context(ref):
    context = mock.Mock()
    context.resource = 'databases/documents/' + ref
    return context

def generate_window_document(windows: list, fid: str) -> dict:
    for i, w in enumerate(windows):
        wid = str(fid) + '_' + str(i)
        doc = {
            'wid': str(wid),
            'fid': str(fid),
            'status': 'new',
            'ppg': list(w),
            'vpg': [0],
            'apg': [0],
            'ppg_scaled': [0],
            'vpg_scaled': [0],
            'apg_scaled': [0],
            'abp': [0],
            'abp': [0],
            'f0': 0,
            'snr': 0,
            'beat_sim': 0,
            'notches': False,
            'flat_lines': True,
        }
        yield doc

def _hash_obj(obj):
    uid = hashlib.sha256(
        json.dumps(sorted({str(obj): obj})).encode("utf-8")
    ).hexdigest()
    return uid
