import json

from typing import Union
from decimal import Decimal
from urllib.parse import urlparse

def is_valid_json(json_obj: Union[str, dict]) -> bool:

    if isinstance(json_obj, dict):
        return True
    if isinstance(json_obj, str):
        try:
            json.loads(json_obj)
            return True
        except (ValueError, TypeError):
            return False

    return False

def is_valid_url(url):
        if not url:
            return False

        parsed = urlparse(url)

        if not all([parsed.scheme, parsed.netloc]):
            return False

        return True

def is_valid_percentage(value):
    try:
        decimal_value = Decimal(value)
        return 0 <= decimal_value <= 1 and len(value.split('.')[1]) == 4
    except (ValueError, IndexError):
        return False

def is_valid_amount(value, allow_negative=False):
    try:
        decimal_value = Decimal(value)
        if not allow_negative and decimal_value < 0:
            return False
        return len(value.split('.')[1]) == 2
    except (ValueError, IndexError):
        return False

def is_valid_integer(value):

    if not isinstance(value, int):
        return False
    
    return True

def is_valid_list(value, allow_empty=False):

    if not isinstance(value, list):
        return False
    if not value and not allow_empty:
        return False
    
    return True