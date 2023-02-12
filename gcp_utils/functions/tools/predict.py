import numpy as np
from typing import Dict, List, Union
from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

def get_inputs(data) -> dict:
    ppg = np.array(data["value"]["fields"]["ppg"]["arrayValue"]).reshape(256, 1).tolist()
    vpg = np.array(data["value"]["fields"]["vpg"]["arrayValue"]).reshape(256, 1).tolist()
    apg = np.array(data["value"]["fields"]["apg"]["arrayValue"]).reshape(256, 1).tolist()
    instance_dict = {
        'ppg': ppg,
        'vpg': vpg,
        'apg': apg,
    }
    return instance_dict

def predict_bp(
    project: str,
    endpoint_id: str,
    instances: Union[Dict, List[Dict]],
    location: str = "us-central1",
    api_endpoint: str = "us-central1-aiplatform.googleapis.com",
):
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
    instances = instances if type(instances) == list else [instances]
    instances = [
        json_format.ParseDict(instance_dict, Value()) for instance_dict in instances
    ]
    parameters_dict = {}
    parameters = json_format.ParseDict(parameters_dict, Value())
    endpoint = client.endpoint_path(
        project=project, location=location, endpoint=endpoint_id
    )
    response = client.predict(
        endpoint=endpoint, instances=instances, parameters=parameters
    )

    # The predictions are a google.protobuf.Value representation of the model's predictions.
    pred = list(np.array(response.predictions[0]).flatten())
    return pred
