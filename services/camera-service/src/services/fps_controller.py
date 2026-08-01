from __future__ import annotations

import threading
import time


class FPSController:
    """
    Controls camera frame rate.
    """

    def __init__(
        self,
        target_fps: int = 30,
    ):
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.last_frame_time: dict[str, float] = {}
        self._lock = threading.Lock()

    def should_process(
        self,
        camera_name: str,
    ) -> bool:
        """
        Determine whether the next frame should be processed.
        """

        with self._lock:
            now = time.time()

            last_time = self.last_frame_time.get(
                camera_name,
                0.0,
            )

            if now - last_time >= self.frame_interval:
                self.last_frame_time[camera_name] = now
                return True

            return False

    def set_fps(
        self,
        fps: int,
    ):
        """
        Update target FPS.
        """

        if fps <= 0:
            fps = 30

        with self._lock:
            self.target_fps = fps
            self.frame_interval = 1.0 / fps

    def get_fps(
        self,
    ) -> int:
        """
        Current target FPS.
        """

        return self.target_fps

    def reset(
        self,
        camera_name: str,
    ):
        """
        Reset FPS timer for one camera.
        """

        with self._lock:
            self.last_frame_time.pop(
                camera_name,
                None,
            )

    def reset_all(
        self,
    ):
        """
        Reset all FPS timers.
        """

        with self._lock:
            self.last_frame_time.clear()

    def current_fps(
        self,
    ) -> int:
        """
        Current configured FPS.
        """

        return self.target_fps


fps_controller = FPSController()
