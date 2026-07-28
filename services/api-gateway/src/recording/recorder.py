import os
from datetime import datetime

import cv2


class VideoRecorder:
    """
    Records video frames into an MP4 file.
    """

    def __init__(
        self,
        camera_id: int,
        fps: int = 20,
    ):
        self.camera_id = camera_id
        self.fps = fps

        self.writer = None

        self.recording = False

        self.file_name = ""
        self.file_path = ""

        self.start_time: datetime | None = None

    def start(
        self,
        width: int,
        height: int,
    ):
        """
        Start recording.
        """

        if self.recording:
            return

        directory = os.path.join(
            "storage",
            "recordings",
            f"camera_{self.camera_id}",
        )

        os.makedirs(
            directory,
            exist_ok=True,
        )

        self.file_name = datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4"

        self.file_path = os.path.join(
            directory,
            self.file_name,
        )

        # Video codec
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")

        self.writer = cv2.VideoWriter(
            self.file_path,
            fourcc,
            self.fps,
            (width, height),
        )

        self.recording = True

        self.start_time = datetime.now()

    def write(
        self,
        frame,
    ):
        """
        Write one frame.
        """

        if self.recording and self.writer is not None:
            self.writer.write(frame)

    def stop(self):
        """
        Stop recording and return metadata.
        """

        if not self.recording:
            return None

        self.recording = False

        end_time = datetime.now()

        if self.writer is not None:
            self.writer.release()

        duration = 0.0

        if self.start_time is not None:
            duration = (end_time - self.start_time).total_seconds()

        size = 0.0

        if os.path.exists(self.file_path):
            size = os.path.getsize(self.file_path) / (1024 * 1024)

        return {
            "file_name": self.file_name,
            "file_path": self.file_path,
            "duration": duration,
            "size": size,
            "start_time": self.start_time,
            "end_time": end_time,
        }
