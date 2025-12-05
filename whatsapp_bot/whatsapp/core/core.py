from datetime import time


def _phone_number(phone: str) -> str:
    """Evolution API expects only digits, no + or @c.us"""
    return ''.join(filter(str.isdigit, str(phone)))

# Default business hours:
# business_hours[0] = Monday, ..., [6] = Sunday
BUSINESS_HOURS_DEFAULT = [
    (time(8, 0), time(20, 0)),  # Monday
    (time(8, 0), time(20, 0)),  # Tuesday
    (time(8, 0), time(20, 0)),  # Wednesday
    (time(8, 0), time(20, 0)),  # Thursday
    # (time(9, 0), time(13, 0)), # Friday 
    (time(9, 0), time(17, 0)), # Friday #DEBUG
    (time(0, 0), time(0, 0)),  # Saturday 
    # (time(0, 0), time(23, 40)),  # Saturday # DEBUG
    (time(8, 0), time(20, 0)), #  Sunday
]

