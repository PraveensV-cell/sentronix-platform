from __future__ import annotations

import time
import uuid
from typing import Any

from src.core.config import settings


class ObjectTracker:
    """
    Tracks detected objects across frames.
    """

    def __init__(
        self,
        max_age: int | None = None,
    ):
        self.objects: dict[str, dict[str, Any]] = {}

        self.max_age = max_age if max_age is not None else settings.TRACKER_MAX_AGE

    def update(
        self,
        detections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Update tracked objects.
        """

        if not settings.ENABLE_TRACKING:
            return detections

        timestamp = time.time()

        tracked = []

        for detection in detections:
            object_id = self.find_existing_object(
                detection,
            )

            if object_id is None:
                object_id = str(
                    uuid.uuid4(),
                )

            detection["object_id"] = object_id

            self.objects[object_id] = {
                "detection": detection,
                "updated": timestamp,
            }

            tracked.append(
                detection,
            )

        self.cleanup(
            timestamp,
        )

        return tracked

    def find_existing_object(
        self,
        detection: dict[str, Any],
    ) -> str | None:
        """
        Match detection with existing object.
        """

        bbox = detection.get(
            "bbox",
        )

        if bbox is None:
            return None

        for object_id, data in self.objects.items():
            old_bbox = data["detection"].get(
                "bbox",
            )

            if (
                self.calculate_distance(
                    bbox,
                    old_bbox,
                )
                < 50
            ):
                return object_id

        return None

    def calculate_distance(
        self,
        box1: list,
        box2: list | None,
    ) -> float:
        """
        Calculate bounding box center distance.
        """

        if box2 is None:
            return 9999

        x1 = (box1[0] + box1[2]) / 2

        y1 = (box1[1] + box1[3]) / 2

        x2 = (box2[0] + box2[2]) / 2

        y2 = (box2[1] + box2[3]) / 2

        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    def cleanup(
        self,
        current_time: float,
    ):
        """
        Remove expired objects.
        """

        expired = []

        for object_id, data in list(self.objects.items()):
            if current_time - data["updated"] > self.max_age:
                expired.append(
                    object_id,
                )

        for object_id in expired:
            self.objects.pop(
                object_id,
                None,
            )

    def active_objects(
        self,
    ) -> int:
        """
        Return active tracked objects.
        """

        return len(
            self.objects,
        )

    def reset(
        self,
    ):
        """
        Clear all tracked objects.
        """

        self.objects.clear()


tracker = ObjectTracker()
