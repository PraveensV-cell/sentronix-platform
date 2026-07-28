import os
from pathlib import Path

from src.core.config import settings


class ImageUtils:
    """
    Utility methods for images.
    """

    @staticmethod
    def ensure_output_directory():
        Path(settings.OUTPUT_DIR).mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def output_path(filename: str):
        ImageUtils.ensure_output_directory()

        return os.path.join(
            settings.OUTPUT_DIR,
            filename,
        )
