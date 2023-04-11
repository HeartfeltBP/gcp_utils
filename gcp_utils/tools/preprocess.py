import numpy as np
import pickle as pkl
from typing import Tuple
from database_tools.tools.dataset import ConfigMapper, Window
from database_tools.processing.modify import bandpass
from database_tools.processing.utils import resample_signal

def process_frame(red_frame: list, ir_frame: list, cm: ConfigMapper) -> dict:
    """
    Steps
    -----
    1. Sanitize (handle NaN values)
    2. Clean (remove large spikes)
    3. Resample (bpm fs -> mimic3 fs)
    4. Flip (correct ppg direction)
    5. Filter (Remove noise)
    6. Split into windows
    """
    # 1
    red_frame = np.array(red_frame, dtype=np.float32)
    red_frame[np.isnan(red_frame)] = 0
    ir_frame = np.array(ir_frame, dtype=np.float32)
    ir_frame[np.isnan(ir_frame)] = 0

    # 2
    red_clean = _clean_frame(red_frame, thresh=cm.deploy.clean_thresh)
    ir_clean = _clean_frame(ir_frame, thresh=cm.deploy.clean_thresh)

    # 3
    red_resamp = resample_signal(red_clean, fs_old=cm.deploy.bpm_fs, fs_new=cm.data.fs)
    ir_resamp = resample_signal(ir_clean, fs_old=cm.deploy.bpm_fs, fs_new=cm.data.fs)

    # 4
    red_flip = _flip_signal(red_resamp)
    ir_flip = _flip_signal(ir_resamp)

    # 5
    red_filt = bandpass(red_flip, low=cm.data.freq_band[0], high=cm.data.freq_band[1], fs=cm.deploy.bpm_fs, method='butter')
    ir_filt = bandpass(ir_flip, low=cm.data.freq_band[0], high=cm.data.freq_band[1], fs=cm.deploy.bpm_fs, method='butter')

    # 6
    windows = _split_frame(sig=ir_filt, n=int(ir_filt.shape[0] / cm.data.win_len))

    result = {
        'red_frame_spo2': red_clean,
        'ir_frame_spo2': ir_clean,
        'red_frame_for_presentation': red_filt.tolist(),
        'ir_frame_for_presentation': ir_filt.tolist(),
        'frame_for_prediction': ir_filt.tolist(),
        'windows': windows,
    }
    return result

def _clean_frame(sig, thresh):
    """Set points too far from median value to median value."""
    sig = sig.reshape(-1) # must be 1d
    med = np.median(sig)
    mask = np.where( (sig > (med + thresh)) | (sig < (med - thresh)) )
    sig[mask] = med
    return sig

def _flip_signal(sig):
    """Flip signal data but subtracting the maximum value."""
    flipped = np.max(sig) - sig
    return flipped

def _split_frame(sig: np.ndarray, n: int) -> list:
    """Split list into n lists.

    Args:
        sig (list): Data.
        n (int): Number of lists.

    Returns:
        n_sigs (list): Data split in to n lists.
    """
    n_sigs = [s.tolist() for s in np.split(sig, n)]
    return n_sigs

def validate_window(ppg: list, cm: ConfigMapper, force_valid: bool = False) -> dict:
    # convert to numpy array
    ppg = np.array(ppg, dtype=np.float32)

    # bpm_scaling
    with open(cm.deploy.bpm_scaler_path, 'rb') as f:
        scaler = pkl.load(f)
    ppg = np.divide(ppg - scaler[0], scaler[1] - scaler[0])

    # validate window with call to win.valid
    win = Window(ppg, cm, checks=cm.data.checks)
    win.get_peaks()
    status = 'valid' if win.valid else 'invalid'

    # debug mode
    if cm.deploy.force_valid:
        status = 'valid'

    # get model inputs if valid
    if status == 'valid':
        vpg, apg = _get_ppg_derivatives(ppg)
    else:
        vpg, apg = np.array([]), np.array([])

    # scale data with mimic3 training minmax scaler
    ppg_s, vpg_s, apg_s = _scale_data(cm.deploy.enceladus_scaler_path, ppg, vpg, apg)

    flat_lines = not win._flat_check
    result = {
        'status': str(status),
        'vpg': vpg.tolist(),
        'apg': apg.tolist(),
        'ppg_scaled': ppg_s.tolist(),
        'vpg_scaled': vpg_s.tolist(),
        'apg_scaled': apg_s.tolist(),
        'f0': float(win.f0),
        'snr': float(win.snr),
        'beat_sim': float(win.beat_sim),
        'notches': bool(win._notch_check),
        'flat_lines': bool(flat_lines),
    }
    return result

def _get_ppg_derivatives(ppg: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    vpg = np.gradient(ppg, axis=0)  # 1st derivative of ppg
    apg = np.gradient(vpg, axis=0)  # 2nd derivative of vpg
    return (vpg, apg)

def _scale_data(path: str, ppg: np.ndarray, vpg: np.ndarray, apg: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    with open(path, 'rb') as f:
        scalers, _ = pkl.load(f)
    ppg_scaler = scalers['ppg']
    vpg_scaler = scalers['vpg']
    apg_scaler = scalers['apg']
    ppg_s = np.divide(ppg - ppg_scaler[0], ppg_scaler[1] - ppg_scaler[0])
    vpg_s = np.divide(vpg - vpg_scaler[0], vpg_scaler[1] - vpg_scaler[0])
    apg_s = np.divide(apg - apg_scaler[0], apg_scaler[1] - apg_scaler[0])
    return (ppg_s, vpg_s, apg_s)
