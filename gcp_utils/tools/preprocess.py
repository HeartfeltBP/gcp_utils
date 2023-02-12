import sys
sys.path.append('database_tools/')

import numpy as np
import pickle as pkl
from typing import Tuple
from database_tools.preprocessing.datastores import ConfigMapper, Window
from database_tools.preprocessing.functions import bandpass

def validate_window(
    username: str,
    sample_id: int,
    ppg: list,
    config: dict,
) -> dict:
    cm = ConfigMapper(config)

    ppg = bandpass(ppg, low=cm.freq_band[0], high=cm.freq_band[1], fs=cm.fs)
    win = Window(ppg, cm, checks=cm.checks)
    valid = win.valid
    vpg, apg = _get_ppg_derivatives(ppg)

    ppg_s, vpg_s, apg_s = _scale_data(cm.scaler_path, ppg, vpg, apg)

    result = dict(
        username=username,
        sample_id=sample_id,
        valid=valid,
        ppg=ppg,
        vpg=vpg,
        apg=apg,
        ppg_scaled=ppg_s,
        vpg_scaled=vpg_s,
        apg_scaled=apg_s,
        predicted=False,  # set to True once prediction is made
    )
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

    ppg_s = np.multiply(ppg, ppg_scaler[1] - ppg_scaler[0]) + ppg_scaler[0]
    vpg_s = np.multiply(vpg, vpg_scaler[1] - vpg_scaler[0]) + vpg_scaler[0]
    apg_s = np.multiply(apg, apg_scaler[1] - apg_scaler[0]) + apg_scaler[0]
    return (ppg_s, vpg_s, apg_s)
