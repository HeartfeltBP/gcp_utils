def default_to_json(x):
    if isinstance(x, int):
        data = {'integerValue': x}
        return data
    elif isinstance(x, str):
        data = {'stringValue': x}
        return data
    elif isinstance(x, bool):
        data = {'booleanValue': x}
        return data
    elif isinstance(x, list):
        data = {'arrayValue': {'values': [{'doubleValue': xx} for xx in x]}}
        return data
    else:
        raise TypeError(f'Type \'{type(x)}\' is not a supported type')

def format_as_json(doc) -> dict:
    if not isinstance(doc, dict):
        doc = [x.to_dict() for x in doc][0]
    data = {'value': {'fields':
        {key: default_to_json(value) for key, value in doc.items()}
    }}
    return data
