import re
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def transform_percentage(value):
    """
    Transform percentage strings (e.g., "2.5%") into decimal strings (e.g., "0.0250").
    """
    if "%" in value:
        match = re.match(r'^(-?\d+(\.\d+)?)%$', value.strip())
        if not match:
            raise ValidationError(f"Invalid percentage format (e.g., '2.5%').")
        percentage = float(match.group(1))
        return f"{percentage / 100:.4f}"
    return value

def transform_currency(value):
    """
    Transform currency strings (e.g., "$2.50") into decimal strings (e.g., "2.50").
    """
    if "$" in value:
        match = re.match(r'^(-?)\$?(\d+(\.\d+)?)$', value.strip())
        if not match:
            raise ValidationError(f"Invalid currency format (e.g., '$1000.00', '-$1000').")
        sign = "-" if match.group(1) == "-" else ""
        amount = float(match.group(2))
        return f"{sign}{amount:.2f}"
    return value

def transform_field(field_name, value):
    """
    Apply transformation logic to a field based on its intended format.
    """
    if isinstance(value, str):
        value = value.strip()

        # Check if the value is a percentage or currency
        if "%" in value:
            return transform_percentage(value)
        if "$" in value:
            return transform_currency(value)

    # Default to decimal transformation
    return (value)

def display_field(field_name, value):
    """
    Transform raw decimal values into user-friendly formats for display.
    """
    if value is None:
        return ""

    if field_name.endswith('_pct'):
        return f"{float(value) * 100:.2f}%"
    elif field_name.endswith('_amt'):
        sign = "-" if float(value) < 0 else ""
        return f"{sign}${abs(float(value)):.2f}"

    return value