def default_to_json(x, name):
    if isinstance(x, int):
        data = {name: {'integerValue': x}}
        return data
    if isinstance(x, str):
        data = {name: {'stringValue': x}}
        return data
    if isinstance(x, bool):
        data = {name: {'booleanValue': x}}
        return data
    if isinstance(x, list):
        data = {'arrayValue': {'values': [{'doubleValue': xx} for xx in x]}}
        return data
