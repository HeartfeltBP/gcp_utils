import numpy as np
import pickle as pkl
from typing import Tuple
from database_tools.preprocessing.datastores import ConfigMapper, Window
from database_tools.preprocessing.functions import bandpass
from database_tools.preprocessing.utils import resample_signal

def process_frame(red_frame, ir_frame, config):
    cm = ConfigMapper(config)
    red_filt = bandpass(red_frame, low=cm.freq_band[0], high=cm.freq_band[1], fs=cm.bpm_fs)
    ir_filt = bandpass(ir_frame, low=cm.freq_band[0], high=cm.freq_band[1], fs=cm.bpm_fs)

    red_filt_flip = _flip_signal(red_filt)
    ir_filt_flip = _flip_signal(ir_filt)
    combined = (red_filt_flip + ir_filt_flip) / 2  # averaging strategy

    combined_resamp = resample_signal(sig=combined.tolist(), fs_old=cm.bpm_fs, fs_new=cm.fs)

    windows = _split_frame(sig=combined_resamp, n=int(combined_resamp.shape[0] / cm.win_len))
    result = {
        'red_frame_for_processing': list(red_filt),
        'ir_frame_for_processing': list(ir_filt),
        'red_frame_for_presentation': list(red_filt_flip),
        'ir_frame_for_presentation': list(ir_filt_flip),
        'combined_frame_for_presentation': list(combined),
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

def validate_window(ppg: list, config: dict) -> dict:
    cm = ConfigMapper(config)

    ppg = np.array(ppg, dtype=np.float32)
    ppg[np.isnan(ppg)] = 0
    ppg = bandpass(ppg, low=cm.freq_band[0], high=cm.freq_band[1], fs=cm.fs)

    win = Window(ppg, cm, checks=cm.checks)
    status = 'valid' if win.valid else 'invalid'
    vpg, apg = _get_ppg_derivatives(ppg)

    ppg_s, vpg_s, apg_s = _scale_data(cm.scaler_path, ppg, vpg, apg)

    result = {
        'status': str(status),
        'ppg': list(ppg),
        'vpg': list(vpg),
        'apg': list(apg),
        'ppg_scaled': list(ppg_s),
        'vpg_scaled': list(vpg_s),
        'apg_scaled': list(apg_s),
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
