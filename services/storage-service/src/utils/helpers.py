from pathlib import Path
from uuid import uuid4


def generate_filename(
    filename: str,
) -> str:
    """
    Generate a unique filename.
    """

    extension = Path(filename).suffix

    return f"{uuid4()}{extension}"


def allowed_extension(
    filename: str,
    allowed: list[str],
) -> bool:
    """
    Validate file extension.
    """

    extension = Path(filename).suffix.lower()

    return extension in allowed


def file_size_mb(
    size: int,
) -> float:
    """
    Convert bytes to MB.
    """

    return round(size / (1024 * 1024), 2)
