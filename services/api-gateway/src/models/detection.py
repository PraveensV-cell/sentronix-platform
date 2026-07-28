from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.base import Base

if TYPE_CHECKING:
    from src.models.camera import Camera
    from src.models.alert import Alert


class Detection(Base):
    """
    Stores AI detection results.
    """

    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    camera_id: Mapped[int] = mapped_column(
        ForeignKey(
            "cameras.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    x1: Mapped[int] = mapped_column(Integer)
    y1: Mapped[int] = mapped_column(Integer)
    x2: Mapped[int] = mapped_column(Integer)
    y2: Mapped[int] = mapped_column(Integer)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ----------------------------------
    # Relationships
    # ----------------------------------

    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="detections",
    )

    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="detection",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Detection("
            f"id={self.id}, "
            f"label='{self.label}', "
            f"confidence={self.confidence:.2f}"
            f")>"
        )
