from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2

from src.services.camera_service import camera_service


class RecordingService:
    """
    Handles camera recording.
    """

    def __init__(self):
        self.recordings = {}
        self.output_dir = Path("recordings")
        self.output_dir.mkdir(
            exist_ok=True,
        )

    def start_recording(
        self,
        camera_name: str,
    ) -> dict:
        """
        Start recording a camera.
        """

        if camera_name in self.recordings:
            return {
                "success": False,
                "message": "Camera is already recording.",
            }

        camera = camera_service.cameras.get(
            camera_name,
        )

        if camera is None:
            return {
                "success": False,
                "message": "Camera not found.",
            }

        capture = cv2.VideoCapture(
            camera.camera_url,
        )

        if not capture.isOpened():
            return {
                "success": False,
                "message": "Unable to open camera.",
            }

        width = int(
            capture.get(
                cv2.CAP_PROP_FRAME_WIDTH,
            )
        )

        height = int(
            capture.get(
                cv2.CAP_PROP_FRAME_HEIGHT,
            )
        )

        fps = capture.get(
            cv2.CAP_PROP_FPS,
        )

        if fps <= 0:
            fps = 30.0

        filename = f"{camera_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        filepath = self.output_dir / filename

        writer = cv2.VideoWriter(
            str(filepath),
            cv2.VideoWriter_fourcc(
                *"mp4v",
            ),
            fps,
            (width, height),
        )

        self.recordings[camera_name] = {
            "capture": capture,
            "writer": writer,
            "file": str(filepath),
        }

        return {
            "success": True,
            "message": "Recording started.",
            "file": str(filepath),
        }

    def write_frame(
        self,
        camera_name: str,
        frame,
    ):
        """
        Write one frame.
        """

        recording = self.recordings.get(
            camera_name,
        )

        if recording is None:
            return

        recording["writer"].write(
            frame,
        )

    def stop_recording(
        self,
        camera_name: str,
    ) -> dict:
        """
        Stop recording.
        """

        recording = self.recordings.get(
            camera_name,
        )

        if recording is None:
            return {
                "success": False,
                "message": "Recording not found.",
            }

        recording["capture"].release()
        recording["writer"].release()

        filepath = recording["file"]

        del self.recordings[camera_name]

        return {
            "success": True,
            "message": "Recording stopped.",
            "file": filepath,
        }

    def is_recording(
        self,
        camera_name: str,
    ) -> bool:
        """
        Check recording state.
        """

        return camera_name in self.recordings

    def active_recordings(
        self,
    ) -> int:
        """
        Number of active recordings.
        """

        return len(
            self.recordings,
        )


recording_service = RecordingService()
