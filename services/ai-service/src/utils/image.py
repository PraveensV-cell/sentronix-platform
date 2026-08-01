from __future__ import annotations

from pathlib import Path

from src.core.config import settings


class ImageUtils:
    """
    Utility methods for image file handling.
    """

    @staticmethod
    def ensure_output_directory() -> Path:
        """
        Create output directory if missing.
        """

        output_dir = Path(
            settings.OUTPUT_DIR,
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return output_dir

    @staticmethod
    def output_path(
        filename: str,
    ) -> str:
        """
        Return output image path.
        """

        output_dir = ImageUtils.ensure_output_directory()

        return str(
            output_dir / filename,
        )
