from sqlalchemy.orm import Session

from src.models.system_health import SystemHealth


class SystemHealthRepository:
    """
    Handles database operations for system health.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        health: SystemHealth,
    ) -> SystemHealth:
        """
        Save a new health snapshot.
        """

        self.db.add(health)
        self.db.commit()
        self.db.refresh(health)

        return health

    def get_all(self):
        """
        Return all health snapshots.
        """

        return (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).all()
        )

    def get_latest(self):
        """
        Return the latest system health snapshot.
        """

        return (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).first()
        )

    def get_by_id(
        self,
        health_id: int,
    ):
        """
        Return a health snapshot by ID.
        """

        return self.db.query(SystemHealth).filter(SystemHealth.id == health_id).first()

    def update(
        self,
        health: SystemHealth,
    ) -> SystemHealth:
        """
        Update a health snapshot.
        """

        self.db.commit()
        self.db.refresh(health)

        return health

    def delete(
        self,
        health: SystemHealth,
    ):
        """
        Delete a health snapshot.
        """

        self.db.delete(health)
        self.db.commit()

    def delete_old_records(
        self,
        keep_last: int = 1000,
    ):
        """
        Keep only the latest health records.
        """

        records = (
            self.db.query(SystemHealth).order_by(SystemHealth.created_at.desc()).all()
        )

        if len(records) <= keep_last:
            return

        for record in records[keep_last:]:
            self.db.delete(record)

        self.db.commit()
