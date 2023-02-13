def default_to_json(x, name):
    if isinstance(x, int):
        data = {name: {'integerValue': x}}
        return data
    elif isinstance(x, str):
        data = {name: {'stringValue': x}}
        return data
    elif isinstance(x, bool):
        data = {name: {'booleanValue': x}}
        return data
    elif isinstance(x, list):
        data = {'arrayValue': {'values': [{'doubleValue': xx} for xx in x]}}
        return data
    else:
        raise TypeError(f'Type \'{type(x)}\' is not a supported type')