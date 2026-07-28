from pathlib import Path


class MetadataService:
    def metadata(
        self,
        path: str,
    ):

        file = Path(path)

        if not file.exists():
            return None

        stat = file.stat()

        return {
            "name": file.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
        }

    def event_metadata(
        self,
        event,
    ):

        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "camera_id": event.camera_id,
            "detections": len(event.detections),
            "created_at": event.created_at,
        }


metadata_service = MetadataService()
