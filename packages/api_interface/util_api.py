import json

def is_valid_json(json_obj):
    if isinstance(json_obj, str):
        try:
            json.loads(json_obj)
            return True
        except ValueError:
            return False
    elif isinstance(json_obj, dict):
        return True
    else:
        return False