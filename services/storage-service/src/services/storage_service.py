import uuid
from datetime import datetime

from src.core.logger import logger
from src.schemas.storage import StorageCreate
from src.schemas.storage import StorageEventRequest
from src.schemas.storage import StorageResponse
from src.services.file_manager import file_manager
from src.services.metadata_service import metadata_service


class StorageService:
    def __init__(self):

        self.files: list[StorageResponse] = []

        self.event_files: list[StorageEventRequest] = []

        file_manager.create_storage_structure()

    def store(
        self,
        request: StorageCreate,
    ) -> StorageResponse:

        file = StorageResponse(
            file_id=str(uuid.uuid4()),
            filename=request.filename,
            category=request.category,
            path=request.path,
            size=request.size,
            uploaded_at=datetime.utcnow(),
        )

        self.files.append(file)

        logger.info(f"Stored File : {file.filename}")

        return file

    def get_all(self):

        return self.files

    def get(
        self,
        file_id: str,
    ):

        for file in self.files:
            if file.file_id == file_id:
                return file

        return None

    def delete(
        self,
        file_id: str,
    ) -> bool:

        for file in self.files:
            if file.file_id == file_id:
                self.files.remove(file)

                return True

        return False

    # ==========================================================
    # Detection Event Storage
    # ==========================================================

    def store_event(
        self,
        event: StorageEventRequest,
    ):

        self.event_files.append(event)

        metadata = metadata_service.metadata("storage/events")

        logger.info(f"Detection Event Stored : {event.event_id}")

        return {
            "message": "Detection event stored successfully.",
            "total_events": len(self.event_files),
            "metadata": metadata,
        }

    def get_event_files(
        self,
    ):

        return self.event_files


storage_service = StorageService()
