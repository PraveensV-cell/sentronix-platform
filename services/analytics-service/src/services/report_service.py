from datetime import datetime


class ReportService:
    def generate(self):

        return {
            "generated_at": datetime.utcnow(),
            "report": {
                "daily_events": 245,
                "detections": 892,
                "camera_utilization": "84%",
                "device_health": "Healthy",
                "storage_usage": "148.7 GB",
                "stored_images": 892,
                "stored_videos": 17,
                "stored_snapshots": 154,
                "notifications_sent": 154,
                "average_confidence": "91%",
                "average_inference_ms": 41,
                "uptime": "99.94%",
            },
        }
