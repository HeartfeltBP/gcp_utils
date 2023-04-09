import numpy as np
import pickle as pkl
from typing import Tuple
from database_tools.tools.dataset import ConfigMapper, Window
from database_tools.processing.modify import bandpass
from database_tools.processing.utils import resample_signal

def process_frame(red_frame: list, ir_frame: list, cm: ConfigMapper) -> dict:
    # sanitize data (for spo2 calculation)
    red_frame = np.array(red_frame, dtype=np.float32)
    red_frame[np.isnan(red_frame)] = 0
    ir_frame = np.array(ir_frame, dtype=np.float32)
    ir_frame[np.isnan(ir_frame)] = 0

    # bandpass and flip (for presentation)
    red_filt = bandpass(red_frame, low=cm.data.freq_band[0], high=cm.data.freq_band[1], fs=cm.deploy.bpm_fs)
    ir_filt = bandpass(ir_frame, low=cm.data.freq_band[0], high=cm.data.freq_band[1], fs=cm.deploy.bpm_fs)
    red_filt_flip = _flip_signal(red_filt)
    ir_filt_flip = _flip_signal(ir_filt)

    # combine wavelengths (for presentation)
    combined = (red_filt_flip + ir_filt_flip) / 2  # averaging strategy

    # resample and split into windows (for bp prediction)
    combined_resamp = resample_signal(sig=combined, fs_old=cm.deploy.bpm_fs, fs_new=cm.data.fs)
    windows = _split_frame(sig=combined_resamp, n=int(combined_resamp.shape[0] / cm.data.win_len))

    result = {
        'red_frame_for_processing': red_frame.tolist(),
        'ir_frame_for_processing': ir_frame.tolist(),
        'red_frame_for_presentation': red_filt_flip.tolist(),
        'ir_frame_for_presentation': ir_filt_flip.tolist(),
        'combined_frame_for_presentation': combined.tolist(),
        'combined_frame_for_processing': combined_resamp.tolist(),
        'windows': windows,
    }
    return result

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

def validate_window(ppg: list, cm: ConfigMapper) -> dict:
    # convert to numpy array
    ppg = np.array(ppg, dtype=np.float32)

    # validate window with call to win.valid
    win = Window(ppg, cm, checks=cm.data.checks)
    win.get_peaks()
    status = 'valid' if win.valid else 'invalid'

    # get model inputs if valid
    if status == 'valid':
        vpg, apg = _get_ppg_derivatives(ppg)
    else:
        vpg, apg = [], []

    # scale data with mimic3 training minmax scaler
    ppg_s, vpg_s, apg_s = _scale_data(cm.deploy.cloud_scaler_path, ppg, vpg, apg)

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
    }
    return result

def _get_ppg_derivatives(ppg: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    vpg = np.gradient(ppg, axis=0)  # 1st derivative of ppg
    apg = np.gradient(vpg, axis=0)  # 2nd derivative of vpg
    return (vpg, apg)

def _scale_data(path: str, ppg: np.ndarray, vpg: np.ndarray, apg: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    with open(path, 'rb') as f:
        scalers = pkl.load(f)
    ppg_scaler = scalers['ppg']
    vpg_scaler = scalers['vpg']
    apg_scaler = scalers['apg']
    ppg_s = np.divide(ppg - ppg_scaler[0], ppg_scaler[1] - ppg_scaler[0])
    vpg_s = np.divide(vpg - vpg_scaler[0], vpg_scaler[1] - vpg_scaler[0])
    apg_s = np.divide(apg - apg_scaler[0], apg_scaler[1] - apg_scaler[0])
    return (ppg_s, vpg_s, apg_s)
