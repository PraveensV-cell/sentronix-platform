from __future__ import annotations

import time

import cv2
from fastapi.responses import StreamingResponse

from src.services.camera_connection_manager import (
    camera_connection_manager,
)
from src.services.camera_health_service import (
    camera_health_service,
)
from src.services.camera_service import camera_service
from src.services.frame_buffer import (
    frame_buffer,
)
from src.services.frame_processor import (
    frame_processor,
)
from src.services.frame_queue import (
    frame_queue,
)
from src.services.fps_controller import (
    fps_controller,
)
from src.services.snapshot_service import (
    snapshot_service,
)


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

        camera = camera_service.get_camera(
            camera_name,
        )

        if camera is None:
            raise ValueError("Camera not found.")

        capture = camera_connection_manager.connect(
            camera_name,
        )

        self.active_streams[camera_name] = capture

        try:
            while capture.isOpened():
                start_time = time.perf_counter()

                success, frame = capture.read()

                if not success:
                    break

                if not fps_controller.should_process(
                    camera_name,
                ):
                    continue

                # ----------------------------
                # Frame Processing
                # ----------------------------

                frame = frame_processor.resize(
                    frame,
                )

                frame = frame_processor.enhance(
                    frame,
                )

                frame = frame_processor.compress(
                    frame,
                )

                # ----------------------------
                # Store Frame
                # ----------------------------

                frame_buffer.update(
                    camera_name,
                    frame,
                )

                frame_queue.push(
                    camera_name,
                    frame,
                )

                # ----------------------------
                # Encode Frame
                # ----------------------------

                success, buffer = cv2.imencode(
                    ".jpg",
                    frame,
                )

                if not success:
                    continue

                latency = time.perf_counter() - start_time

                camera_health_service.update(
                    camera_name=camera_name,
                    fps=fps_controller.get_fps(),
                    connected=True,
                    latency=latency,
                )

                frame_bytes = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )

        finally:
            camera_health_service.update(
                camera_name=camera_name,
                fps=0,
                connected=False,
                latency=0,
            )

            frame_buffer.remove(
                camera_name,
            )

            frame_queue.clear(
                camera_name,
            )

            fps_controller.reset(
                camera_name,
            )

            camera_connection_manager.disconnect(
                camera_name,
            )

            self.active_streams.pop(
                camera_name,
                None,
            )

    def capture_snapshot(
        self,
        camera_name: str,
    ) -> str | None:
        """
        Capture a snapshot from the latest frame.
        """

        frame = frame_buffer.get(
            camera_name,
        )

        if frame is None:
            return None

        return snapshot_service.save(
            camera_name,
            frame,
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

        camera_health_service.update(
            camera_name=camera_name,
            fps=0,
            connected=False,
            latency=0,
        )

        camera_connection_manager.disconnect(
            camera_name,
        )

        frame_buffer.remove(
            camera_name,
        )

        frame_queue.clear(
            camera_name,
        )

        fps_controller.reset(
            camera_name,
        )

        self.active_streams.pop(
            camera_name,
            None,
        )

        return True

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
