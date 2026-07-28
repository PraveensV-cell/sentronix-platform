from src.services.metrics_service import MetricsService
from src.services.report_service import ReportService


class AnalyticsService:
    def __init__(self):

        self.metrics_service = MetricsService()

        self.report_service = ReportService()

        self.received_events = []

    def summary(self):

        metrics = self.metrics_service.metrics()

        return {
            "events": metrics["events"],
            "detections": metrics["detections"],
            "cameras": metrics["cameras"],
            "devices": metrics["devices"],
            "storage_gb": metrics["storage_gb"],
        }

    def metrics(self):

        return self.metrics_service.metrics()

    def report(self):

        return self.report_service.generate()

    # ==========================================================
    # Detection Events
    # ==========================================================

    def add_event(
        self,
        event,
    ):

        self.received_events.append(event)

        return {
            "message": "Analytics updated successfully.",
            "total_events": len(self.received_events),
        }

    def get_events(
        self,
    ):

        return self.received_events
