from datetime import datetime
from zoneinfo import ZoneInfo


def get_utc_now() -> datetime:
    """
    Get the current date and time in UTC.

    This function returns the current time with timezone information set to UTC,
    ensuring that the returned datetime object is offset-aware.
    """
    return datetime.now(ZoneInfo("UTC"))
