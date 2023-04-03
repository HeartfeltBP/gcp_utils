import numpy as np
import pickle as pkl
from typing import Dict, List, Union, Tuple
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from neurokit2.ppg.ppg_findpeaks import _ppg_findpeaks_bishop

def predict_cardiac_values(frame: List[list], fs: int) -> Tuple[int, float, float]:
    ppg_red = frame[0]
    ppg_ir = frame[1]
    try:
        red_idx = _find_peaks(ppg_red)
        ir_idx = _find_peaks(ppg_ir)

        pulse_rate_multiplier = 60 / (len(frame) / fs)
        pulse_rate = int(len(red_idx) * pulse_rate_multiplier)

        spo2, r = _predict_spo2(ppg_red, ppg_ir, red_idx, ir_idx)
        return (pulse_rate, spo2, r)
    except Exception as e:
        return (-1, -1, -1)

def _predict_spo2(ppg_red, ppg_ir, red_idx, ir_idx) -> Tuple[float, float]:
    """Estimate absorbtion and SpO2.

    Args:
        ppg_red (list): PPG data (red LED).
        ppg_ir (list): PPG data (infrared LED).
        red_idx (dict): Peak data for ppg_red.
        ir_idx (dict): Peak data for ppg_ir.

    Returns:
        spo2 (float): SpO2 as a percentage.
        r (float): Absorption.
    """
    red_peaks, red_troughs = red_idx['peaks'], red_idx['troughs']
    red_high, red_low = np.max(ppg_red[red_peaks]), np.min(ppg_red[red_troughs])

    ir_peaks, ir_troughs = ir_idx['peaks'], ir_idx['troughs']
    ir_high, ir_low = np.max(ppg_ir[ir_peaks]), np.min(ppg_ir[ir_troughs])

    ac_red = red_high - red_low
    ac_ir = ir_high - ir_low

    r = ( ac_red / red_low ) / ( ac_ir / ir_low )
    spo2 = 104 - (17 * r)
    return (spo2, r)

def _find_peaks(ppg_cleaned, show=False, **kwargs):
    """Modified version of neuroki2 ppg_findpeaks method. Returns peaks and troughs
       instead of just peaks. See neurokit2 documentation for original function.
    """
    peaks, troughs = _ppg_findpeaks_bishop(ppg_cleaned, show=show, **kwargs)
    return dict(peaks=peaks[0], troughs=troughs[0])

def predict_bp(data, config):
    instances = _get_inputs(data)
    abp_scaled = _predict(
        project="123543907199",
        endpoint_id="4207052545266286592",
        location="us-central1",
        instances=instances,
    )
    abp = _rescale_bp(config['scaler_path'], abp_scaled)
    result = {
        u'status': 'predicted',
        u'abp_scaled': abp_scaled,
        u'abp': abp,
    }
    return result

def _get_inputs(data) -> dict:
    """Takes data from firestore in JSON format and formats as model instance.

    Args:
        data: Firestore document data.

    Returns:
        dict: Instance for inference.
    """
    ppg = np.array([float(x['doubleValue']) for x in data["value"]["fields"]["ppg_scaled"]["arrayValue"]['values']], dtype=np.float32)
    vpg = np.array([float(x['doubleValue']) for x in data["value"]["fields"]["vpg_scaled"]["arrayValue"]['values']], dtype=np.float32)
    apg = np.array([float(x['doubleValue']) for x in data["value"]["fields"]["apg_scaled"]["arrayValue"]['values']], dtype=np.float32)
    instances = [{
        'ppg': ppg.reshape(256, 1).tolist(),
        'vpg': vpg.reshape(256, 1).tolist(),
        'apg': apg.reshape(256, 1).tolist(),
    }]
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
    pred = np.array(response.predictions[0]).flatten()
    return pred.tolist()

def _rescale_bp(path: str, abp: np.ndarray) -> np.ndarray:
    with open(path, 'rb') as f:
        scalers = pkl.load(f)
    abp_scaler = scalers['abp']
    abp_s = np.multiply(abp, abp_scaler[1] - abp_scaler[0]) + abp_scaler[0]
    return abp_s.tolist()
