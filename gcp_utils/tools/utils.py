import math
import numpy as np
from scipy import signal

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
    else:
        raise TypeError(f'Type \'{type(x)}\' is not a supported type')

def format_as_json(doc) -> dict:
    if not isinstance(doc, dict):
        doc = [x.to_dict() for x in doc][0]
    data = {'value': {'fields':
        {key: default_to_json(value) for key, value in doc.items()}
    }}
    return data

def resample_raw_window(sig: list, fs_old: int, fs_new: int, t: float = 2.048) -> list:
    """Resample a signal to a new sampling rate. This is done with the context
       of a reference length of time in order to produce a result that is
       evenly divisible by the window length (at the new sampling rate).

    Args:
        sig (list): Data.
        fs_old (int): Old sampling rate.
        fs_new (int): New sampling rate.
        t (float, optional): Window length in seconds. Defaults to 2.048.

    Returns:
        resamp (list): Resampled signal.
    """
    old_win_len = fs_old * t
    new_win_len = fs_new * t
    n = int( (len(sig) / old_win_len) * new_win_len )
    resamp = signal.resample(sig, n)
    resamp = list(resamp)
    return resamp

def split_raw_window(sig: list, n: int) -> list:
    """Split list into n lists.

    Args:
        sig (list): Data.
        n (int): Number of lists.

    Returns:
        n_sigs (list): Data split in to n lists.
    """
    sig = np.array(sig, dtype=np.float32)
    n_sigs = [list(s) for s in np.split(sig, n)]
    return n_sigs
