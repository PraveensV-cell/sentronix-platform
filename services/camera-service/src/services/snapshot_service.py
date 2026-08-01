from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2


class SnapshotService:
    """
    Handles camera snapshots.
    """

    def __init__(self):
        self.output = Path("snapshots")
        self.output.mkdir(
            exist_ok=True,
        )

    def save(
        self,
        camera_name: str,
        frame,
    ) -> str:

        filename = f"{camera_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        path = self.output / filename

        cv2.imwrite(
            str(path),
            frame,
        )

        return str(path)


snapshot_service = SnapshotService()
