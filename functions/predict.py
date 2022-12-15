import keras
import numpy as np
import pickle as pkl
from heartpy.preprocessing import flip_signal
from heartpy.peakdetection import detect_peaks
from heartpy.datautils import rolling_mean

def predict(data, model_path, scaler_path):
    ppg = data['ppg']
    vpg = data['vpg']
    apg = data['apg']

    with open(scaler_path, 'rb') as f:
        scalers = pkl.load(f)
    ppg_scaler = scalers['ppg']
    vpg_scaler = scalers['vpg']
    apg_scaler = scalers['apg']
    abp_scaler = scalers['abp']
    
    ppg_input = np.divide(ppg - ppg_scaler[0], ppg_scaler[1] - ppg_scaler[0])
    vpg_input = np.divide(vpg - vpg_scaler[0], vpg_scaler[1] - vpg_scaler[0])
    apg_input = np.divide(apg - apg_scaler[0], apg_scaler[1] - apg_scaler[0])

    model = keras.models.load_model(model_path)
    pred = model.predict([ppg_input, vpg_input, apg_input]).reshape(-1, 256)
    abp = np.multiply(pred, abp_scaler[1] - abp_scaler[0]) + abp_scaler[0]

    fs=125
    windowsize=1
    ma_perc=20
    pad_width = 19
    x_pad = np.pad(abp, pad_width=[pad_width, 0], constant_values=[abp[0]])
    x_pad = np.pad(x_pad, pad_width=[0, pad_width], constant_values=[abp[-1]])

    rol_mean = rolling_mean(x_pad, windowsize=windowsize, sample_rate=fs)
    peaks = detect_peaks(x_pad, rol_mean, ma_perc=ma_perc, sample_rate=fs)['peaklist']
    peaks = np.array(peaks) - pad_width - 1

    flip = flip_signal(x_pad)
    rol_mean = rolling_mean(flip, windowsize=windowsize, sample_rate=fs)
    valleys = detect_peaks(flip, rol_mean, ma_perc=ma_perc, sample_rate=fs)['peaklist']
    valleys = np.array(valleys) - pad_width - 1

    sbp = np.mean(abp[peaks]) if len(peaks) > 0 else -1
    dbp = np.mean(abp[valleys]) if len(valleys) > 0 else -1
    return dict(ppg_input=ppg_input, vpg_input=vpg_input, apg_input=apg_input, pred=pred, abp=abp, sbp=sbp, dbp=dbp)