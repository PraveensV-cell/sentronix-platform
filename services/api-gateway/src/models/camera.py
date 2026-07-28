from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.base import Base

from src.models.recording import Recording

if TYPE_CHECKING:
    from src.models.alert import Alert
    from src.models.detection import Detection
    from src.models.recording import Recording


class Camera(Base):
    """
    Camera model.
    """

    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    rtsp_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    camera_type: Mapped[str] = mapped_column(
        String(50),
        default="rtsp",
    )

    zone: Mapped[str] = mapped_column(
        String(100),
        default="Default",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="offline",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ----------------------------------
    # Relationships
    # ----------------------------------

    detections: Mapped[list["Detection"]] = relationship(
        "Detection",
        back_populates="camera",
        cascade="all, delete-orphan",
    )

    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="camera",
        cascade="all, delete-orphan",
    )

    recordings: Mapped[list["Recording"]] = relationship(
        "Recording",
        back_populates="camera",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Camera("
            f"id={self.id}, "
            f"name='{self.name}', "
            f"location='{self.location}', "
            f"status='{self.status}'"
            f")>"
        )
