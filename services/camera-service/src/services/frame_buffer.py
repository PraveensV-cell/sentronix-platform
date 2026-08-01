from __future__ import annotations

import threading

import cv2


class FrameBuffer:
    """
    Stores the latest frame for each camera.
    """

    def __init__(self):
        self._frames: dict[str, cv2.typing.MatLike] = {}
        self._lock = threading.Lock()

    def update(
        self,
        camera_name: str,
        frame,
    ):
        """
        Update latest frame.
        """

        with self._lock:
            self._frames[camera_name] = frame

    def get(
        self,
        camera_name: str,
    ):
        """
        Get latest frame.
        """

        with self._lock:
            return self._frames.get(camera_name)

    def remove(
        self,
        camera_name: str,
    ):
        """
        Remove frame.
        """

        with self._lock:
            self._frames.pop(
                camera_name,
                None,
            )

    def clear(
        self,
    ):
        """
        Clear all frames.
        """

        with self._lock:
            self._frames.clear()


frame_buffer = FrameBuffer()
