from pathlib import Path

from src.core.logger import logger


class FileManager:
    def create_directory(
        self,
        directory: str,
    ):

        Path(directory).mkdir(
            parents=True,
            exist_ok=True,
        )

    def create_storage_structure(self):

        directories = [
            "storage",
            "storage/events",
            "storage/images",
            "storage/videos",
            "storage/snapshots",
            "storage/evidence",
            "storage/temp",
        ]

        for directory in directories:
            self.create_directory(directory)

        logger.info("Storage directory structure verified.")

    def file_exists(
        self,
        path: str,
    ) -> bool:

        return Path(path).exists()

    def register_file(
        self,
        path: str,
    ):

        file = Path(path)

        file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not file.exists():
            file.touch()

        logger.info(f"Registered file : {path}")

        return str(file)

    def delete_file(
        self,
        path: str,
    ) -> bool:

        file = Path(path)

        if not file.exists():
            return False

        file.unlink()

        logger.info(f"Deleted {path}")

        return True


file_manager = FileManager()
