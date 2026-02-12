from datetime import datetime, timezone


def utc_now() -> datetime:
    """UTC aware datetime, compatible with Python 3.14 deprecation guidance."""
    return datetime.now(timezone.utc)
