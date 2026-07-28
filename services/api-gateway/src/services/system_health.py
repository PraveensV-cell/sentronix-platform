from sqlalchemy.orm import Session

from src.models.system_health import SystemHealth
from src.repositories.system_health_repository import (
    SystemHealthRepository,
)
from src.schemas.system_health import (
    SystemHealthCreate,
    SystemHealthUpdate,
)


class SystemHealthService:
    """
    Business logic for System Health.
    """

    def __init__(self, db: Session):
        self.repository = SystemHealthRepository(db)

    def create_health(
        self,
        health_data: SystemHealthCreate,
    ) -> SystemHealth:
        """
        Create a new health snapshot.
        """

        health = SystemHealth(
            cpu_usage=health_data.cpu_usage,
            memory_usage=health_data.memory_usage,
            disk_usage=health_data.disk_usage,
            network_usage=health_data.network_usage,
            uptime=health_data.uptime,
            database_status=health_data.database_status,
            ai_status=health_data.ai_status,
        )

        return self.repository.create(health)

    def list_health(self):
        """
        Return all health records.
        """

        return self.repository.get_all()

    def get_latest_health(self):
        """
        Return the latest health snapshot.
        """

        return self.repository.get_latest()

    def get_health(
        self,
        health_id: int,
    ):
        """
        Return a health snapshot by ID.
        """

        return self.repository.get_by_id(health_id)

    def update_health(
        self,
        health_id: int,
        health_data: SystemHealthUpdate,
    ):
        """
        Update an existing health record.
        """

        health = self.repository.get_by_id(health_id)

        if health is None:
            return None

        if health_data.cpu_usage is not None:
            health.cpu_usage = health_data.cpu_usage

        if health_data.memory_usage is not None:
            health.memory_usage = health_data.memory_usage

        if health_data.disk_usage is not None:
            health.disk_usage = health_data.disk_usage

        if health_data.network_usage is not None:
            health.network_usage = health_data.network_usage

        if health_data.uptime is not None:
            health.uptime = health_data.uptime

        if health_data.database_status is not None:
            health.database_status = health_data.database_status

        if health_data.ai_status is not None:
            health.ai_status = health_data.ai_status

        return self.repository.update(health)

    def delete_health(
        self,
        health_id: int,
    ) -> bool:
        """
        Delete a health record.
        """

        health = self.repository.get_by_id(health_id)

        if health is None:
            return False

        self.repository.delete(health)

        return True

    def cleanup_old_records(
        self,
        keep_last: int = 1000,
    ):
        """
        Remove old health records.
        """

        self.repository.delete_old_records(
            keep_last=keep_last,
        )
