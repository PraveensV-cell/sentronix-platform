import threading
import time

from src.database.session import SessionLocal
from src.monitor.ai_monitor import AIMonitor
from src.monitor.camera_monitor import CameraMonitor
from src.monitor.database_monitor import DatabaseMonitor
from src.monitor.system_monitor import SystemMonitor
from src.schemas.system_health import SystemHealthCreate
from src.services.system_health import SystemHealthService


class SystemHealthWorker:
    """
    Background worker that periodically collects
    system health metrics and stores them.
    """

    def __init__(self):

        self.running = False

        self.thread = None

        self.interval = 30

        self.system_monitor = SystemMonitor()

        self.ai_monitor = AIMonitor()

        self.camera_monitor = CameraMonitor()

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.run,
            daemon=True,
        )

        self.thread.start()

        print("[HealthWorker] Started")

    def stop(self):

        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2)

        print("[HealthWorker] Stopped")

    def run(self):

        while self.running:
            db = SessionLocal()

            try:
                database_monitor = DatabaseMonitor(db)

                system_data = self.system_monitor.collect()

                database_data = database_monitor.collect()

                ai_data = self.ai_monitor.collect()

                camera_data = self.camera_monitor.collect()

                service = SystemHealthService(db)

                service.create_health(
                    SystemHealthCreate(
                        cpu_usage=system_data["cpu_usage"],
                        memory_usage=system_data["memory_usage"],
                        disk_usage=system_data["disk_usage"],
                        network_usage=system_data["network_usage"],
                        uptime=system_data["uptime"],
                        database_status=database_data["status"],
                        ai_status=ai_data["status"],
                    )
                )

                service.cleanup_old_records(
                    keep_last=1000,
                )

                print(
                    "[HealthWorker]",
                    {
                        "system": system_data,
                        "database": database_data,
                        "ai": ai_data,
                        "cameras": camera_data,
                    },
                )

            except Exception as exc:
                print(f"[HealthWorker] {exc}")

            finally:
                db.close()

            time.sleep(self.interval)


system_health_worker = SystemHealthWorker()
