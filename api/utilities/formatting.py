import datetime

from datetime import timezone
from decimal import Decimal


def from_timestamp(ts):
    """Convert a timestamp to a datetime object."""
    return None if ts == 0 else datetime.datetime.fromtimestamp(ts, tz=timezone.utc)

def to_decimal(value):
    """Convert a blockchain integer value to a formatted decimal string."""
    return f"{Decimal(value) / 100:.2f}"
