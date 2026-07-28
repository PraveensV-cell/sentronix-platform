import time

from sqlalchemy import text
from sqlalchemy.orm import Session


class DatabaseMonitor:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def is_connected(self) -> bool:

        try:
            self.db.execute(text("SELECT 1"))
            return True

        except Exception:
            return False

    def get_latency(self) -> float:

        try:
            start = time.perf_counter()

            self.db.execute(text("SELECT 1"))

            end = time.perf_counter()

            return round(
                (end - start) * 1000,
                2,
            )

        except Exception:
            return -1.0

    def get_status(self) -> str:

        return "ONLINE" if self.is_connected() else "OFFLINE"

    def collect(self) -> dict:

        return {
            "status": self.get_status(),
            "latency_ms": self.get_latency(),
        }
