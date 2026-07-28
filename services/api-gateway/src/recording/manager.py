import threading
import time

from src.database.session import SessionLocal
from src.recording.recorder import VideoRecorder
from src.schemas.recording import RecordingCreate
from src.services.recording import RecordingService


class RecordingManager:
    def __init__(self):
        self.recorders = {}
        self.max_duration = 30

    def start_recording(self, camera_id: int, frame):

        if camera_id in self.recorders:
            return

        height, width = frame.shape[:2]

        recorder = VideoRecorder(camera_id)
        recorder.start(width, height)

        self.recorders[camera_id] = recorder

        threading.Thread(
            target=self._auto_stop,
            args=(camera_id,),
            daemon=True,
        ).start()

    def write_frame(self, camera_id: int, frame):

        recorder = self.recorders.get(camera_id)

        if recorder:
            recorder.write(frame)

    def stop_recording(self, camera_id: int):

        recorder = self.recorders.get(camera_id)

        if recorder is None:
            return None

        metadata = recorder.stop()

        del self.recorders[camera_id]

        return metadata

    def _auto_stop(self, camera_id: int):

        time.sleep(self.max_duration)

        metadata = self.stop_recording(camera_id)

        if metadata is None:
            return

        db = SessionLocal()

        try:
            service = RecordingService(db)

            service.create_recording(
                RecordingCreate(
                    camera_id=camera_id,
                    file_name=metadata["file_name"],
                    file_path=metadata["file_path"],
                    duration=metadata["duration"],
                    size=metadata["size"],
                    start_time=metadata["start_time"],
                    end_time=metadata["end_time"],
                )
            )

            print(f"[Recording] Saved: {metadata['file_name']}")

        finally:
            db.close()


recording_manager = RecordingManager()
