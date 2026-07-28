from __future__ import annotations

import cv2

from fastapi.responses import StreamingResponse

from src.services.camera_service import camera_service


class CameraStreamService:
    """
    Handles live camera streaming.
    """

    def __init__(self):
        self.active_streams = {}

    def generate_frames(
        self,
        camera_name: str,
    ):
        """
        Generate MJPEG frames.
        """

        camera = camera_service.cameras.get(camera_name)

        if camera is None:
            raise ValueError("Camera not found.")

        capture = cv2.VideoCapture(
            camera.camera_url,
        )

        self.active_streams[camera_name] = capture

        while capture.isOpened():
            success, frame = capture.read()

            if not success:
                break

            _, buffer = cv2.imencode(
                ".jpg",
                frame,
            )

            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

        capture.release()

        self.active_streams.pop(
            camera_name,
            None,
        )

    def stream(
        self,
        camera_name: str,
    ):
        """
        Return StreamingResponse.
        """

        return StreamingResponse(
            self.generate_frames(
                camera_name,
            ),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    def stop_stream(
        self,
        camera_name: str,
    ):
        """
        Stop streaming.
        """

        capture = self.active_streams.get(
            camera_name,
        )

        if capture:
            capture.release()

            self.active_streams.pop(
                camera_name,
                None,
            )

            return True

        return False

    def active_count(
        self,
    ) -> int:
        """
        Number of active streams.
        """

        return len(
            self.active_streams,
        )


camera_stream_service = CameraStreamService()
