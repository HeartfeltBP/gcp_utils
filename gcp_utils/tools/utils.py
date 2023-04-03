import json
import hashlib
import numpy as np
from scipy import signal
from typing import Tuple

def hash_obj(obj):
    uid = hashlib.sha256(
        json.dumps(sorted({str(obj): obj})).encode("utf-8")
    ).hexdigest()
    return uid

def get_document_context(context):
    path_parts = context.resource.split('/documents/')[1].split('/')
    collection_path = path_parts[0]
    document_path = '/'.join(path_parts[1:])
    return (collection_path, document_path)

def default_to_json(x):
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
    else:
        raise TypeError(f'Type \'{type(x)}\' is not a supported type')

def format_as_json(doc) -> dict:
    if isinstance(doc, list):
        n_docs = doc
    elif not isinstance(doc, dict):
        n_docs = [x.to_dict() for x in doc]
    else:
        n_docs = [doc]
    data = [{'value': {'fields':
        {key: default_to_json(value) for key, value in doc.items()}
    }} for doc in n_docs]
    return data

def resample_frame(sig: list, fs_old: int, fs_new: int) -> Tuple[list, int]:
    """Resample a signal to a new sampling rate. This is done with the context
       of a reference length of time in order to produce a result that is
       evenly divisible by the window length (at the new sampling rate).

    Args:
        sig (list): Data.
        fs_old (int): Old sampling rate.
        fs_new (int): New sampling rate.

    Returns:
        resamp (list): Resampled signal.
    """
    frame_len = len(sig)
    frame_time = frame_len / fs_old
    resamp = signal.resample(sig, int(round(frame_time * fs_new, -1))).tolist()
    return resamp

def split_frame(sig: list, n: int) -> list:
    """Split list into n lists.

    Args:
        sig (list): Data.
        n (int): Number of lists.

    Returns:
        n_sigs (list): Data split in to n lists.
    """
    sig = np.array(sig, dtype=np.float32)
    n_sigs = [s.tolist() for s in np.split(sig, n)]
    return n_sigs

def generate_sample_document(samples: list, fid: str) -> dict:
    for s in samples:
        doc = {
            'sid': str(hash_obj(s)),
            'fid': str(fid),
            'status': 'new',
            'ppg_raw': list(s),
            'ppg': [0],
            'vpg': [0],
            'apg': [0],
            'ppg_scaled': [0],
            'vpg_scaled': [0],
            'apg_scaled': [0],
            'abp_scaled': [0],
            'abp': [0],
            'hr': 0,
            'snr': 0,
            'beat_sim': 0,
        }
        yield doc
