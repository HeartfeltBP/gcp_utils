import numpy as np
from typing import Dict, List, Union
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

def get_inputs(data) -> dict:
    ppg = np.array([float(x['doubleValue']) for x in data["value"]["fields"]["ppg_scaled"]["arrayValue"]['values']][0:256], dtype=np.float32)
    vpg = np.array([float(x['doubleValue']) for x in data["value"]["fields"]["vpg_scaled"]["arrayValue"]['values']][0:256], dtype=np.float32)
    apg = np.array([float(x['doubleValue']) for x in data["value"]["fields"]["apg_scaled"]["arrayValue"]['values']][0:256], dtype=np.float32)
    instance_dict = [{
        'ppg': ppg.reshape(256, 1).tolist(),
        'vpg': vpg.reshape(256, 1).tolist(),
        'apg': apg.reshape(256, 1).tolist(),
    }]
    return instance_dict

def predict_bp(
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
