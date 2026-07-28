import cv2

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.services.camera import CameraService
from src.streaming.manager import stream_manager

router = APIRouter(
    prefix="/stream",
    tags=["Streaming"],
)


@router.post("/{camera_id}/start")
def start_stream(
    camera_id: int,
    db: Session = Depends(get_db),
):
    """
    Start streaming a camera.
    """

    service = CameraService(db)

    camera = service.get_camera(camera_id)

    if camera is None:
        raise HTTPException(
            status_code=404,
            detail="Camera not found",
        )

    stream_manager.start_stream(
        camera.id,
        camera.rtsp_url,
    )

    return {
        "success": True,
        "message": "Camera stream started.",
    }


@router.post("/{camera_id}/stop")
def stop_stream(camera_id: int):
    """
    Stop streaming a camera.
    """

    stream_manager.stop_stream(camera_id)

    return {
        "success": True,
        "message": "Camera stream stopped.",
    }


def generate_frames(camera_id: int):
    """
    MJPEG frame generator.
    """

    stream = stream_manager.get_stream(camera_id)

    if stream is None:
        return

    while True:
        frame = stream.get_frame()

        if frame is None:
            continue

        success, buffer = cv2.imencode(
            ".jpg",
            frame,
        )

        if not success:
            continue

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@router.get("/{camera_id}/live")
def live_stream(camera_id: int):
    """
    Live MJPEG stream.
    """

    stream = stream_manager.get_stream(camera_id)

    if stream is None:
        raise HTTPException(
            status_code=404,
            detail="Stream not running.",
        )

    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/{camera_id}/snapshot")
def snapshot(camera_id: int):
    """
    Return latest frame.
    """

    stream = stream_manager.get_stream(camera_id)

    if stream is None:
        raise HTTPException(
            status_code=404,
            detail="Stream not running.",
        )

    frame = stream.get_frame()

    if frame is None:
        raise HTTPException(
            status_code=404,
            detail="No frame available.",
        )

    _, buffer = cv2.imencode(
        ".jpg",
        frame,
    )

    return Response(
        content=buffer.tobytes(),
        media_type="image/jpeg",
    )
