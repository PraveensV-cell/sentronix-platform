from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from src.database.base import Base


class SystemHealth(Base):
    """
    Stores system health snapshots.
    """

    __tablename__ = "system_health"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    cpu_usage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    memory_usage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    disk_usage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    network_usage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    uptime: Mapped[str] = mapped_column(
        String(100),
        default="0s",
    )

    database_status: Mapped[str] = mapped_column(
        String(20),
        default="UNKNOWN",
    )

    ai_status: Mapped[str] = mapped_column(
        String(20),
        default="UNKNOWN",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    def __repr__(self):
        return (
            f"<SystemHealth("
            f"cpu={self.cpu_usage}%, "
            f"memory={self.memory_usage}%, "
            f"disk={self.disk_usage}%"
            f")>"
        )
