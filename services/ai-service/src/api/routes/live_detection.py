from __future__ import annotations

import cv2

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.services.live_detection_service import (
    live_detection_service,
)


router = APIRouter(
    prefix="/detect",
    tags=["Live Detection"],
)


def generate_frames(
    source: int | str = 0,
):
    """
    Generate live detection frames.
    """

    for data in live_detection_service.start(
        source,
    ):
        frame = data["frame"].copy()

        detections = data.get(
            "detections",
            [],
        )

        for detection in detections:
            bbox = detection.get(
                "bbox",
            )

            if not bbox:
                continue

            x1, y1, x2, y2 = map(
                int,
                bbox,
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2,
            )

            label = (
                f"{detection.get('label', 'object')} {detection.get('confidence', 0)}"
            )

            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
        )

        if not success:
            continue

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@router.get("/live")
def live_detection(
    source: int | str = 0,
):
    """
    Start live AI detection stream.
    """

    return StreamingResponse(
        generate_frames(
            source,
        ),
        media_type=("multipart/x-mixed-replace; boundary=frame"),
    )


@router.get("/live/status")
def live_status():
    """
    Get active live detection streams.
    """

    return {
        "active_streams": live_detection_service.active_count(),
    }
