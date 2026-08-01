from __future__ import annotations

from datetime import datetime
from typing import Any


class TrackingService:
    """
    Handles object tracking history.
    """

    def __init__(
        self,
        max_history: int = 100,
    ):
        self.history: dict[str, list[dict[str, Any]]] = {}

        self.max_history = max(
            max_history,
            1,
        )

    def update(
        self,
        detections: list[dict[str, Any]],
    ) -> None:
        """
        Store tracked object information.
        """

        timestamp = datetime.utcnow().isoformat()

        for detection in detections:
            object_id = detection.get(
                "object_id",
            )

            if object_id is None:
                continue

            if object_id not in self.history:
                self.history[object_id] = []

            self.history[object_id].append(
                {
                    "timestamp": timestamp,
                    "label": detection.get(
                        "label",
                    ),
                    "confidence": detection.get(
                        "confidence",
                    ),
                    "bbox": detection.get(
                        "bbox",
                    ),
                }
            )

            if (
                len(
                    self.history[object_id],
                )
                > self.max_history
            ):
                self.history[object_id] = self.history[object_id][-self.max_history :]

    def get_history(
        self,
        object_id: str,
    ) -> list[dict[str, Any]]:
        """
        Get object movement history.
        """

        return self.history.get(
            object_id,
            [],
        )

    def get_all(
        self,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Return all tracked objects.
        """

        return self.history

    def remove(
        self,
        object_id: str,
    ) -> list[dict[str, Any]] | None:
        """
        Remove tracked object history.
        """

        return self.history.pop(
            object_id,
            None,
        )

    def clear(
        self,
    ) -> None:
        """
        Clear all tracking history.
        """

        self.history.clear()

    def active_objects(
        self,
    ) -> int:
        """
        Number of tracked objects.
        """

        return len(
            self.history,
        )

    def statistics(
        self,
    ) -> dict[str, int]:
        """
        Tracking statistics.
        """

        return {
            "active_objects": len(
                self.history,
            ),
            "total_history_entries": sum(len(items) for items in self.history.values()),
        }


tracking_service = TrackingService()
