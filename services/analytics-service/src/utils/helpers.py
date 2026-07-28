from datetime import datetime


def current_timestamp() -> str:
    """
    Return current UTC timestamp.
    """

    return datetime.utcnow().isoformat()


def percentage(value: float, total: float) -> float:
    """
    Calculate percentage.
    """

    if total <= 0:
        return 0.0

    return round((value / total) * 100, 2)


def bytes_to_gb(size: int) -> float:
    """
    Convert bytes to gigabytes.
    """

    return round(size / (1024**3), 2)
