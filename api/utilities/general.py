import random

def find_match(items, key, value, return_key, default):
    """Find matching item in a list and return specified key."""
    match = next((item for item in items if item.get(key) == value), None)
    return match.get(return_key) if match else default

def generate_random_time():
    """Generate a random time in HH:MM:SS format."""
    return f"{random.randint(0, 23):02}:{random.randint(0, 59):02}:{random.randint(0, 59):02}"