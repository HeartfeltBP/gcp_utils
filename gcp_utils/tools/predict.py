import numpy as np
import pickle as pkl
from typing import Dict, List, Union
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from database_tools.processing.detect import detect_peaks
from database_tools.tools.dataset import ConfigMapper

def predict_cardiac_metrics(red: list, ir: list, red_idx: list, ir_idx: list, cm: ConfigMapper) -> dict:
    red, ir = np.array(red), np.array(ir)
    pulse_rate = _calc_pulse_rate(ir_idx, fs=cm.deploy.bpm_fs)
    spo2, r = _calc_spo2(red, ir, red_idx, ir_idx)
    result = {
        'pulse_rate': int(pulse_rate),
        'spo2': float(spo2),
        'r': float(r)
    }
    return result

def _calc_pulse_rate(idx, fs):
    pulse_rate = fs / np.mean(np.diff(idx['peaks'])) * 60
    return pulse_rate

def _calc_spo2(ppg_red, ppg_ir, red_idx, ir_idx, method='linear'):
    red_peaks, red_troughs = red_idx['peaks'], red_idx['troughs']
    ir_peaks, ir_troughs = ir_idx['peaks'], ir_idx['troughs']

    # choose where to calculate based on shorted list
    options = [red_peaks, red_troughs, ir_peaks, ir_troughs]
    lengths = [len(x) for x in options]

    # Return error code if missing needed value
    if 0 in lengths:
        return (-1, -1)

    i = int(len(options[np.argmin(lengths)]) / 2)

    red_high, red_low = np.max(ppg_red[red_peaks[i]]), np.min(ppg_red[red_troughs[i]])
    ir_high, ir_low = np.max(ppg_ir[ir_peaks[i]]), np.min(ppg_ir[ir_troughs[i]])

    ac_red = red_high - red_low
    ac_ir = ir_high - ir_low

    r = ( ac_red / red_low ) / ( ac_ir / ir_low )

    if method == 'linear':
        spo2 = round(104 - (17 * r), 1)
    elif method == 'curve':
        spo2 = (1.596 * (r ** 2)) + (-34.670 * r) + 112.690
    return (spo2, r)

def predict_bp(data: dict):
    instances = _get_inputs(data)
    try:
        abp = _predict(
            project="123543907199",
            endpoint_id="4207052545266286592",
            location="us-central1",
            instances=instances,
        )
    except Exception as e:
        abp = [dict(abp=np.zeros((256)).tolist(), sbp=-2, dbp=-2) for i in range(len(instances))]

    result = []
    for i in abp:
        peaks, troughs = detect_peaks(i).values()
        if (len(peaks) > 0) & (len(troughs) > 0):
            sbp, dbp = int(np.mean(i[peaks])), int(np.mean(i[troughs]))
        else:
            sbp, dbp = -1, -1
        result.append(dict(abp=i.tolist(), sbp=sbp, dbp=dbp))
    return result

def _get_inputs(data) -> dict:
    """Takes data from firestore in JSON format and formats as model instance.

    Args:
        data: Firestore document data.

    Returns:
        dict: Instance for inference.
    """
    instances = []
    for d in data:
        ppg = np.array([float(x['doubleValue']) for x in d["value"]["fields"]["ppg_scaled"]["arrayValue"]['values']], dtype=np.float32)
        vpg = np.array([float(x['doubleValue']) for x in d["value"]["fields"]["vpg_scaled"]["arrayValue"]['values']], dtype=np.float32)
        apg = np.array([float(x['doubleValue']) for x in d["value"]["fields"]["apg_scaled"]["arrayValue"]['values']], dtype=np.float32)
        instances.append({
            'ppg': ppg.reshape(256, 1).tolist(),
            'vpg': vpg.reshape(256, 1).tolist(),
            'apg': apg.reshape(256, 1).tolist(),
        })
    return instances

def _predict(
    project: str,
    endpoint_id: str,
    instances: Union[Dict, List[Dict]],
    location: str = "us-central1",
    api_endpoint: str = "us-central1-aiplatform.googleapis.com",
) -> list:
    """
    `instances` can be either single instance of type dict or a list
    of instances.
    """
    # The AI Platform services require regional API endpoints.
    client_options = {"api_endpoint": api_endpoint}
    # Initialize client that will be used to create and send requests.
    # This client only needs to be created once, and can be reused for multiple requests.
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    # The format of each instance should conform to the deployed model's prediction input schema.
    parameters_dict = {}
    parameters = json_format.ParseDict(parameters_dict, Value())
    endpoint = client.endpoint_path(
        project=project, location=location, endpoint=endpoint_id
    )
    response = client.predict(
        endpoint=endpoint, instances=instances, parameters=parameters
    )

    # The predictions are a google.protobuf.Value representation of the model's predictions.
    pred = np.array(response.predictions).reshape(-1, 256)
    return pred
