from datetime import datetime


class ScheduledRecordingService:
    """
    Scheduled recording placeholder.
    """

    def schedule(
        self,
        camera_name: str,
        start_time: datetime,
        end_time: datetime,
    ):

        return {
            "camera": camera_name,
            "start": start_time,
            "end": end_time,
            "status": "Scheduled",
        }


scheduled_recording_service = ScheduledRecordingService()
