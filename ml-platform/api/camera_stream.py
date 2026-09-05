import threading
import time
from pathlib import Path

import cv2
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(
    prefix="/stream",
    tags=["Camera Stream"],
)

CAMERAS = {
    "camera_01": 0,
}

camera_instances = {}
camera_locks = {}
camera_threads = {}
camera_frames = {}
camera_running = {}


def get_camera(
    camera_id,
):
    if camera_id not in camera_instances:
        source = CAMERAS.get(camera_id)

        if source is None:
            return None

        camera = cv2.VideoCapture(source)

        if not camera.isOpened():
            camera.release()
            return None

        camera_instances[camera_id] = camera

        camera_locks[camera_id] = threading.Lock()

        camera_frames[camera_id] = None

        camera_running[camera_id] = True

        thread = threading.Thread(
            target=camera_worker,
            args=(camera_id,),
            daemon=True,
        )

        camera_threads[camera_id] = thread

        thread.start()

    return camera_instances.get(camera_id)


def camera_worker(
    camera_id,
):
    camera = camera_instances.get(camera_id)

    if camera is None:
        return

    while camera_running.get(
        camera_id,
        False,
    ):
        success, frame = camera.read()

        if not success:
            time.sleep(0.1)
            continue

        lock = camera_locks.get(camera_id)

        if lock is None:
            continue

        with lock:
            camera_frames[camera_id] = frame

        time.sleep(0.01)


def generate_frames(
    camera_id,
):
    camera = get_camera(camera_id)

    if camera is None:
        return

    while camera_running.get(
        camera_id,
        False,
    ):
        frame = None

        lock = camera_locks.get(camera_id)

        if lock is not None:
            with lock:
                current_frame = camera_frames.get(camera_id)

                if current_frame is not None:
                    frame = current_frame.copy()

        if frame is None:
            time.sleep(0.05)
            continue

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
        )

        if not success:
            continue

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
        )

        time.sleep(0.03)


def stop_camera(
    camera_id,
):
    camera_running[camera_id] = False

    camera = camera_instances.get(camera_id)

    if camera is not None:
        camera.release()

    camera_instances.pop(
        camera_id,
        None,
    )

    camera_locks.pop(
        camera_id,
        None,
    )

    camera_threads.pop(
        camera_id,
        None,
    )

    camera_frames.pop(
        camera_id,
        None,
    )


@router.get("")
def stream_status():
    cameras = []

    for camera_id in CAMERAS:
        cameras.append(
            {
                "camera_id": camera_id,
                "active": camera_running.get(
                    camera_id,
                    False,
                ),
            }
        )

    return {
        "service": "Sentronix Camera Stream",
        "status": "running",
        "cameras": cameras,
    }


@router.get("/{camera_id}")
def camera_stream(
    camera_id: str,
):
    if camera_id not in CAMERAS:
        return {
            "success": False,
            "message": "Camera not found",
            "camera_id": camera_id,
        }

    return StreamingResponse(
        generate_frames(camera_id),
        media_type=("multipart/x-mixed-replace; boundary=frame"),
    )


@router.post("/{camera_id}/start")
def start_camera(
    camera_id: str,
):
    if camera_id not in CAMERAS:
        return {
            "success": False,
            "message": "Camera not found",
        }

    camera = get_camera(camera_id)

    if camera is None:
        return {
            "success": False,
            "message": "Unable to open camera",
        }

    return {
        "success": True,
        "message": "Camera started",
        "camera_id": camera_id,
    }


@router.post("/{camera_id}/stop")
def stop_camera_endpoint(
    camera_id: str,
):
    if camera_id not in CAMERAS:
        return {
            "success": False,
            "message": "Camera not found",
        }

    stop_camera(camera_id)

    return {
        "success": True,
        "message": "Camera stopped",
        "camera_id": camera_id,
    }


@router.get("/{camera_id}/status")
def camera_stream_status(
    camera_id: str,
):
    if camera_id not in CAMERAS:
        return {
            "success": False,
            "message": "Camera not found",
        }

    active = camera_running.get(
        camera_id,
        False,
    )

    frame_available = camera_frames.get(camera_id) is not None

    return {
        "success": True,
        "camera_id": camera_id,
        "active": active,
        "frame_available": frame_available,
    }
