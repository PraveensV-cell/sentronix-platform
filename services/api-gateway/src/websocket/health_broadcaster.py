import asyncio

from src.database.session import SessionLocal
from src.monitor.ai_monitor import AIMonitor
from src.monitor.camera_monitor import CameraMonitor
from src.monitor.database_monitor import DatabaseMonitor
from src.monitor.system_monitor import SystemMonitor
from src.websocket import manager


class HealthBroadcaster:
    """
    Broadcasts system health to all connected
    WebSocket clients.
    """

    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.ai_monitor = AIMonitor()
        self.camera_monitor = CameraMonitor()

    async def broadcast(self):

        db = SessionLocal()

        try:
            database_monitor = DatabaseMonitor(db)

            payload = {
                "type": "system_health",
                "system": self.system_monitor.collect(),
                "database": database_monitor.collect(),
                "ai": self.ai_monitor.collect(),
                "cameras": self.camera_monitor.collect(),
            }

            await manager.broadcast(payload)

        finally:
            db.close()

    async def run(self):

        while True:
            try:
                await self.broadcast()

            except Exception as exc:
                print(f"[HealthBroadcaster] {exc}")

            await asyncio.sleep(30)


health_broadcaster = HealthBroadcaster()
