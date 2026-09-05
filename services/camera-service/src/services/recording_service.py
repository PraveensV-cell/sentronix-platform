from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2

from src.services.camera_connection_manager import (
    camera_connection_manager,
)
from src.services.camera_service import camera_service


class RecordingService:
    """
    Handles camera recording.
    """

    def __init__(self):
        self.recordings = {}
        self.recording_history = []
        self.recording_metadata = {}

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

        camera = camera_service.get_camera(
            camera_name,
        )

        if camera is None:
            return {
                "success": False,
                "message": "Camera not found.",
            }

        try:
            capture = camera_connection_manager.connect(
                camera_name,
            )

        except Exception:
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
            cv2.VideoWriter_fourcc(  # type: ignore
                *"mp4v",
            ),
            fps,
            (width, height),
        )

        self.recordings[camera_name] = {
            "writer": writer,
            "file": str(filepath),
            "started_at": datetime.now(),
            "frames": 0,
        }

        self.recording_metadata[camera_name] = {
            "camera": camera_name,
            "file": str(filepath),
            "started_at": datetime.now().isoformat(),
            "status": "Recording",
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

        recording["frames"] += 1

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

        camera_connection_manager.disconnect(
            camera_name,
        )

        recording["writer"].release()

        filepath = recording["file"]

        metadata = self.recording_metadata.get(
            camera_name,
        )

        if metadata:
            metadata["status"] = "Completed"

            metadata["ended_at"] = datetime.now().isoformat()

            metadata["frames"] = recording["frames"]

            self.recording_history.append(
                metadata,
            )

            self.recording_metadata.pop(
                camera_name,
                None,
            )

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

    def active_metadata(
        self,
    ):
        """
        Get active recording metadata.
        """

        return list(
            self.recording_metadata.values(),
        )

    def history(
        self,
    ):
        """
        Get recording history.
        """

        return self.recording_history

    def recording_info(
        self,
        camera_name: str,
    ):
        """
        Get one recording information.
        """

        return self.recording_metadata.get(
            camera_name,
        )


recording_service = RecordingService()
