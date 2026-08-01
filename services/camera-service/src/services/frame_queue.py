from __future__ import annotations

from collections import deque
import threading


class FrameQueue:
    """
    Stores frames for each camera.
    """

    def __init__(
        self,
        max_size: int = 30,
    ):
        self._queues = {}
        self._lock = threading.Lock()
        self.max_size = max_size

    def push(
        self,
        camera_name: str,
        frame,
    ):
        """
        Add frame to queue.
        """

        with self._lock:
            if camera_name not in self._queues:
                self._queues[camera_name] = deque(
                    maxlen=self.max_size,
                )

            self._queues[camera_name].append(
                frame,
            )

    def pop(
        self,
        camera_name: str,
    ):
        """
        Get oldest frame.
        """

        with self._lock:
            queue = self._queues.get(
                camera_name,
            )

            if not queue:
                return None

            if len(queue) == 0:
                return None

            return queue.popleft()

    def size(
        self,
        camera_name: str,
    ) -> int:
        """
        Queue size.
        """

        with self._lock:
            queue = self._queues.get(
                camera_name,
            )

            if queue is None:
                return 0

            return len(queue)

    def clear(
        self,
        camera_name: str,
    ):
        """
        Clear one queue.
        """

        with self._lock:
            self._queues.pop(
                camera_name,
                None,
            )

    def clear_all(
        self,
    ):
        """
        Clear all queues.
        """

        with self._lock:
            self._queues.clear()


frame_queue = FrameQueue()
