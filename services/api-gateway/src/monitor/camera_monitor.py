from datetime import datetime

from src.streaming.manager import stream_manager


class CameraMonitor:
    """
    Monitors all active camera streams.
    """

    def __init__(self):
        pass

    def get_camera_status(
        self,
        camera_id: int,
    ):
        """
        Return health information for a single camera.
        """

        stream = stream_manager.streams.get(camera_id)

        if stream is None:
            return {
                "camera_id": camera_id,
                "status": "OFFLINE",
            }

        frame = stream.get_raw_frame()

        if frame is None:
            return {
                "camera_id": camera_id,
                "status": "NO_FRAME",
            }

        height, width = frame.shape[:2]

        fps = getattr(
            stream,
            "fps",
            0,
        )

        started_at = getattr(
            stream,
            "started_at",
            None,
        )

        uptime = "Unknown"

        if started_at is not None:
            seconds = int((datetime.now() - started_at).total_seconds())

            hours = seconds // 3600

            minutes = (seconds % 3600) // 60

            seconds = seconds % 60

            uptime = f"{hours}h {minutes}m {seconds}s"

        return {
            "camera_id": camera_id,
            "status": "ONLINE",
            "resolution": f"{width}x{height}",
            "fps": fps,
            "uptime": uptime,
            "last_frame": datetime.now().isoformat(),
        }

    def get_all_cameras(self):
        """
        Return all camera statuses.
        """

        cameras = []

        for camera_id in stream_manager.streams.keys():
            cameras.append(self.get_camera_status(camera_id))

        return cameras

    def get_total_cameras(self):
        """
        Total configured camera streams.
        """

        return len(stream_manager.streams)

    def get_online_cameras(self):
        """
        Number of online cameras.
        """

        online = 0

        for camera_id in stream_manager.streams.keys():
            status = self.get_camera_status(camera_id)

            if status["status"] == "ONLINE":
                online += 1

        return online

    def collect(self):
        """
        Collect camera health metrics.
        """

        return {
            "total_cameras": self.get_total_cameras(),
            "online_cameras": self.get_online_cameras(),
            "offline_cameras": (self.get_total_cameras() - self.get_online_cameras()),
            "cameras": self.get_all_cameras(),
        }
