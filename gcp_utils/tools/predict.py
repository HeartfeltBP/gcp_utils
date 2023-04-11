import numpy as np
import pickle as pkl
from typing import Dict, List, Union
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from database_tools.processing.cardiac import estimate_pulse_rate, estimate_spo2
from database_tools.processing.detect import detect_peaks
from database_tools.tools.dataset import ConfigMapper

def predict_cardiac_metrics(red: list, ir: list, cm: ConfigMapper) -> dict:
    red_idx = detect_peaks(np.array(red))
    ir_idx = detect_peaks(np.array(ir))

    pulse_rate = estimate_pulse_rate(red, ir, red_idx, ir_idx, fs=cm.deploy.bpm_fs)
    spo2, r = estimate_spo2(red, ir, red_idx, ir_idx)
    result = {
        'pulse_rate': int(pulse_rate),
        'spo2': float(spo2),
        'r': float(r)
    }
    return result

def predict_bp(data: dict, cm: ConfigMapper):
    instances = _get_inputs(data)
    try:
        abp = _predict(
            project="123543907199",
            endpoint_id="4207052545266286592",
            location="us-central1",
            instances=instances,
        )
    except Exception as e:
        abp = [np.zeros((256)).tolist() for i in range(len(instances))]

    # TODO: Remove this
    if cm.deploy.rescale_bp:
        abp = _rescale_bp(cm.deploy.cloud_scaler_path, abp)

    result = [i.tolist() for i in abp]
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

def _rescale_bp(path: str, abp: np.ndarray) -> np.ndarray:
    with open(path, 'rb') as f:
        scalers, _ = pkl.load(f)
    abp_scaler = scalers['abp']
    abp_s = np.multiply(abp, abp_scaler[1] - abp_scaler[0]) + abp_scaler[0]
    return abp_s.tolist()
