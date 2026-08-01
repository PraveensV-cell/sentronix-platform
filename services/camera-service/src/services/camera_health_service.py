from __future__ import annotations

import time


class CameraHealthService:
    """
    Camera health monitoring.
    """

    def __init__(self):
        self._health = {}

    def update(
        self,
        camera_name: str,
        fps: float,
        connected: bool,
        latency: float,
    ):
        """
        Update camera health.
        """

        self._health[camera_name] = {
            "connected": connected,
            "fps": round(fps, 2),
            "latency": round(latency, 3),
            "last_seen": time.time(),
            "status": "Online" if connected else "Offline",
        }

    def get(
        self,
        camera_name: str,
    ):

        return self._health.get(
            camera_name,
            {
                "status": "Offline",
            },
        )

    def all(self):

        return self._health


camera_health_service = CameraHealthService()
