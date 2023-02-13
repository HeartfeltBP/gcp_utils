import numpy as np
import pickle as pkl
from typing import Tuple
from database_tools.preprocessing.datastores import ConfigMapper, Window
from database_tools.preprocessing.functions import bandpass

def validate_window(
    ppg: list,
    config: dict,
) -> dict:
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
    }
    return result

def _get_ppg_derivatives(ppg: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    vpg = np.gradient(ppg, axis=0)  # 1st derivative of ppg
    apg = np.gradient(vpg, axis=0)  # 2nd derivative of vpg
    return (vpg, apg)

def rescale_data(path: str, abp: np.ndarray) -> np.ndarray:
    with open(path, 'rb') as f:
        scalers = pkl.load(f)
    abp_scaler = scalers['abp']
    abp_s = np.multiply(abp, abp_scaler[1] - abp_scaler[0]) + abp_scaler[0]
    return abp_s

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
