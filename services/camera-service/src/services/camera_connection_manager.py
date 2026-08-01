from __future__ import annotations

import threading
import time

import cv2

from src.services.camera_service import camera_service


class CameraConnectionManager:
    """
    Manages shared camera connections.
    """

    def __init__(self):
        self._connections: dict[str, cv2.VideoCapture] = {}
        self._lock = threading.Lock()

        # RTSP Connection Settings
        self.max_retries = 3
        self.retry_delay = 2

    def connect(
        self,
        camera_name: str,
    ) -> cv2.VideoCapture:
        """
        Open or return an existing camera connection.
        """

        with self._lock:
            if camera_name in self._connections:
                capture = self._connections[camera_name]

                if capture.isOpened():
                    return capture

            camera = camera_service.get_camera(
                camera_name,
            )

            if camera is None:
                raise ValueError("Camera not found.")

            for _ in range(self.max_retries):
                capture = cv2.VideoCapture(
                    camera.camera_url,
                    cv2.CAP_FFMPEG,
                )

                capture.set(
                    cv2.CAP_PROP_BUFFERSIZE,
                    2,
                )

                if capture.isOpened():
                    self._connections[camera_name] = capture

                    return capture

                capture.release()

                time.sleep(
                    self.retry_delay,
                )

            raise ConnectionError(f"Unable to connect to camera: {camera_name}")

    def reconnect(
        self,
        camera_name: str,
    ) -> cv2.VideoCapture:
        """
        Reconnect a camera.
        """

        self.disconnect(
            camera_name,
        )

        return self.connect(
            camera_name,
        )

    def disconnect(
        self,
        camera_name: str,
    ):
        """
        Disconnect one camera.
        """

        with self._lock:
            capture = self._connections.pop(
                camera_name,
                None,
            )

            if capture:
                capture.release()

    def disconnect_all(
        self,
    ):
        """
        Disconnect all cameras.
        """

        with self._lock:
            for capture in self._connections.values():
                capture.release()

            self._connections.clear()

    def cleanup(
        self,
    ):
        """
        Cleanup all camera resources.
        """

        self.disconnect_all()

    def validate_connection(
        self,
        camera_name: str,
    ) -> bool:
        """
        Validate a camera connection.
        """

        capture = self._connections.get(
            camera_name,
        )

        if capture is None:
            return False

        if not capture.isOpened():
            return False

        success, _ = capture.read()

        return success

    def is_connected(
        self,
        camera_name: str,
    ) -> bool:
        """
        Check connection state.
        """

        capture = self._connections.get(
            camera_name,
        )

        return capture is not None and capture.isOpened()

    def active_connections(
        self,
    ) -> int:
        """
        Number of active connections.
        """

        return len(
            self._connections,
        )

    def connection_status(
        self,
        camera_name: str,
    ) -> dict:
        """
        Camera connection status.
        """

        capture = self._connections.get(
            camera_name,
        )

        if capture is None:
            return {
                "connected": False,
                "status": "Disconnected",
            }

        connected = capture.isOpened()

        return {
            "connected": connected,
            "status": "Connected" if connected else "Disconnected",
        }

    def connection_info(
        self,
        camera_name: str,
    ) -> dict:
        """
        Camera connection information.
        """

        capture = self._connections.get(
            camera_name,
        )

        if capture is None:
            return {
                "connected": False,
                "status": "Disconnected",
                "width": 0,
                "height": 0,
                "fps": 0,
            }

        connected = capture.isOpened()

        return {
            "connected": connected,
            "status": "Connected" if connected else "Disconnected",
            "width": int(
                capture.get(
                    cv2.CAP_PROP_FRAME_WIDTH,
                )
            ),
            "height": int(
                capture.get(
                    cv2.CAP_PROP_FRAME_HEIGHT,
                )
            ),
            "fps": capture.get(
                cv2.CAP_PROP_FPS,
            ),
        }

    def connection_count(
        self,
    ) -> dict:
        """
        Camera connection statistics.
        """

        return {
            "active_connections": len(
                self._connections,
            ),
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }

    def discover_usb_cameras(
        self,
        max_devices: int = 10,
    ) -> list[dict]:
        """
        Discover available USB cameras.
        """

        cameras = []

        for index in range(max_devices):
            capture = cv2.VideoCapture(index)

            if capture.isOpened():
                cameras.append(
                    {
                        "index": index,
                        "name": f"USB Camera {index}",
                    }
                )

                capture.release()

        return cameras

    def validate_ip_camera(
        self,
        camera_url: str,
    ) -> bool:
        """
        Validate an IP camera URL.
        """

        capture = cv2.VideoCapture(
            camera_url,
            cv2.CAP_FFMPEG,
        )

        connected = capture.isOpened()

        capture.release()

        return connected

    def auto_reconnect(
        self,
        camera_name: str,
    ) -> bool:
        """
        Automatically reconnect if disconnected.
        """

        if self.is_connected(
            camera_name,
        ):
            return True

        try:
            self.reconnect(
                camera_name,
            )
            return True

        except Exception:
            return False


camera_connection_manager = CameraConnectionManager()
