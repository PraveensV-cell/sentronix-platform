import threading
import time
import sqlite3
from pathlib import Path
import cv2
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.vision_engine import process_frame, generate_synthetic_frame

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/stream",
    tags=["Camera Stream"],
)

camera_instances = {}
camera_locks = {}
camera_threads = {}
camera_frames = {}
camera_running = {}
camera_info = {}


def get_db_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_camera_source_info(camera_id: str):
    conn = get_db_connection()
    try:
        # Try finding by numeric id or camera_id / camera_name
        row = None
        if str(camera_id).isdigit():
            row = conn.execute(
                "SELECT * FROM cameras WHERE id = ?", (int(camera_id),)
            ).fetchone()
        if not row:
            row = conn.execute(
                """
                SELECT * FROM cameras 
                WHERE LOWER(camera_name) LIKE ? OR id = 1
                LIMIT 1
            """,
                (f"%{camera_id}%",),
            ).fetchone()

        if row:
            return dict(row)
        return {
            "id": 1,
            "camera_name": "Entrance Cam 01",
            "source_type": "webcam",
            "source_url": "0",
            "status": "online",
        }
    finally:
        conn.close()


def get_camera(camera_id: str):
    str_id = str(camera_id)
    if str_id not in camera_running or not camera_running[str_id]:
        info = get_camera_source_info(str_id)
        camera_info[str_id] = info

        source = info.get("source_url", "0")
        if str(source).isdigit():
            source = int(source)

        cam_obj = None
        try:
            cam_obj = cv2.VideoCapture(source)
            if not cam_obj.isOpened():
                cam_obj.release()
                cam_obj = None
        except Exception:
            cam_obj = None

        camera_instances[str_id] = cam_obj
        camera_locks[str_id] = threading.Lock()
        camera_frames[str_id] = None
        camera_running[str_id] = True

        thread = threading.Thread(
            target=camera_worker,
            args=(str_id,),
            daemon=True,
        )
        camera_threads[str_id] = thread
        thread.start()

    return True


def camera_worker(camera_id: str):
    str_id = str(camera_id)
    cam = camera_instances.get(str_id)
    info = camera_info.get(str_id, {})
    cam_name = info.get("camera_name", f"Camera {str_id}")
    db_id = info.get("id", 1)

    frame_counter = 0

    while camera_running.get(str_id, False):
        raw_frame = None

        if cam is not None and cam.isOpened():
            success, read_frame = cam.read()
            if success:
                raw_frame = read_frame

        # Fallback to high-fidelity simulated surveillance stream if hardware camera is not available
        if raw_frame is None:
            raw_frame = generate_synthetic_frame(frame_counter, cam_name, db_id)

        # Run multi-stage AI perception (YOLO, Face Detection, Attendance, Alerts)
        processed = process_frame(raw_frame, cam_name, db_id)

        lock = camera_locks.get(str_id)
        if lock is not None:
            with lock:
                camera_frames[str_id] = processed

        frame_counter += 1
        time.sleep(0.04)  # ~25 FPS

    if cam is not None:
        cam.release()


def generate_frames(camera_id: str):
    str_id = str(camera_id)
    get_camera(str_id)

    while camera_running.get(str_id, False):
        frame = None
        lock = camera_locks.get(str_id)
        if lock is not None:
            with lock:
                curr = camera_frames.get(str_id)
                if curr is not None:
                    frame = curr.copy()

        if frame is None:
            time.sleep(0.04)
            continue

        success, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            continue

        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
        )
        time.sleep(0.04)


def stop_camera(camera_id: str):
    str_id = str(camera_id)
    camera_running[str_id] = False
    cam = camera_instances.get(str_id)
    if cam is not None:
        cam.release()
    camera_instances.pop(str_id, None)
    camera_locks.pop(str_id, None)
    camera_threads.pop(str_id, None)
    camera_frames.pop(str_id, None)


@router.get("")
def stream_status():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT id, camera_name, status FROM cameras").fetchall()
        cameras = []
        for r in rows:
            cid = str(r["id"])
            cameras.append(
                {
                    "camera_id": cid,
                    "name": r["camera_name"],
                    "active": camera_running.get(cid, False),
                }
            )
        return {
            "service": "Sentronix AI Real-Time Camera Stream",
            "status": "running",
            "cameras": cameras,
        }
    finally:
        conn.close()


@router.get("/{camera_id}")
def camera_stream(camera_id: str):
    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/{camera_id}/start")
def start_camera(camera_id: str):
    get_camera(str(camera_id))
    return {
        "success": True,
        "message": f"Camera {camera_id} stream started",
        "camera_id": camera_id,
    }


@router.post("/{camera_id}/stop")
def stop_camera_endpoint(camera_id: str):
    stop_camera(str(camera_id))
    return {
        "success": True,
        "message": f"Camera {camera_id} stream stopped",
        "camera_id": camera_id,
    }


@router.get("/{camera_id}/status")
def camera_stream_status(camera_id: str):
    str_id = str(camera_id)
    active = camera_running.get(str_id, False)
    frame_available = camera_frames.get(str_id) is not None
    return {
        "success": True,
        "camera_id": camera_id,
        "active": active,
        "frame_available": frame_available,
    }
