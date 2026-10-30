from datetime import datetime
import os
import socket
import sqlite3
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from api.vision_engine import generate_synthetic_frame, process_frame

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
stream_alert_cooldown = {}
camera_info = {}
mobile_uploaded_frames = {}  # {camera_id: {"frame": np.ndarray, "timestamp": float}}


def get_db_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_local_ip() -> str:
    """Detect local network LAN IP so mobile phones can connect over Wi-Fi."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def get_camera_source_info(camera_id: str):
    conn = get_db_connection()
    try:
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
            "assigned_function": "FACE_ATTENDANCE",
        }
    finally:
        conn.close()


def open_capture_source(source):
    """
    Open webcam / camera source with fallback & DirectShow on Windows.
    Supports laptop built-in webcams, USB webcams, phone RTSP streams, and IP Webcams.
    """
    if source is None:
        source = 0

    # Numeric index (built-in laptop webcam: 0, external USB: 1 or 2)
    if isinstance(source, int) or (isinstance(source, str) and str(source).isdigit()):
        idx = int(source)

        # On Windows, try DirectShow (CAP_DSHOW) first for fast webcam detection & 720p HD
        if os.name == "nt":
            try:
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    return cap
                cap.release()
            except Exception:
                pass

        # Standard OpenCV fallback
        try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                return cap
            cap.release()
        except Exception:
            pass

    # Network Stream: Phone IP Webcam (http://...), DroidCam, or RTSP stream
    elif isinstance(source, str) and (
        source.startswith("http://")
        or source.startswith("https://")
        or source.startswith("rtsp://")
    ):
        try:
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap
            cap.release()
        except Exception:
            pass

    return None


def get_camera(camera_id: str):
    str_id = str(camera_id)
    if str_id not in camera_running or not camera_running[str_id]:
        info = get_camera_source_info(str_id)
        camera_info[str_id] = info

        source = info.get("source_url", "0")
        cam_obj = open_capture_source(source)

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
    source = info.get("source_url", "0")

    frame_counter = 0

    while camera_running.get(str_id, False):
        raw_frame = None

        # 1. Check if a mobile phone or remote browser uploaded a recent frame (< 10.0s ago)
        mobile_data = mobile_uploaded_frames.get(str_id)
        if mobile_data is not None and (time.time() - mobile_data["timestamp"]) < 10.0:
            raw_frame = mobile_data["frame"]

        # 2. If no mobile frame, check hardware webcam / laptop camera
        if raw_frame is None and cam is not None and cam.isOpened():
            success, read_frame = cam.read()
            if success and read_frame is not None and read_frame.size > 0:
                raw_frame = read_frame
            else:
                # Device might have been unplugged or is in use
                cam.release()
                cam = None

        # 3. Dynamic Re-probe: If camera is currently None, attempt reconnection every 50 frames (~2s)
        # This guarantees that when the user plugs in a USB webcam or enables laptop camera, it connects live!
        if raw_frame is None and cam is None and (frame_counter % 50 == 0):
            cam = open_capture_source(source)
            camera_instances[str_id] = cam

        # 4. Fallback: If hardware camera is offline and no mobile feed, use synthetic surveillance feed
        if raw_frame is None:
            raw_frame = generate_synthetic_frame(frame_counter, cam_name, db_id)

        # Run multi-stage AI perception (YOLOv11s, Face Detection, Attendance, Alerts) based on assigned function
        assigned_func = info.get("assigned_function", "FACE_ATTENDANCE")
        processed = process_frame(raw_frame, cam_name, db_id, assigned_func)

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


@router.get("/network-info")
def get_network_info():
    """Returns local network LAN IP and connection URLs for mobile camera usage."""
    local_ip = get_local_ip()
    return {
        "local_ip": local_ip,
        "mobile_dashboard_url": f"http://{local_ip}:5173",
        "api_stream_url": f"http://{local_ip}:8000/stream/1",
        "instructions": {
            "option_1_browser_camera": f"Open http://{local_ip}:5173 on your mobile browser (same Wi-Fi) and tap 'Broadcast Phone Camera'",
            "option_2_ip_webcam_app": "Install free 'IP Webcam' on Android/iOS, tap 'Start Server', and enter the displayed URL (e.g. http://192.168.1.X:8080/video) into Sentronix Camera Manager.",
            "option_3_laptop_webcam": "Make sure Camera index is set to 0 in Camera Devices to use your built-in laptop camera.",
        },
    }


@router.post("/{camera_id}/upload-frame")
async def upload_camera_frame(camera_id: str, file: UploadFile = File(...)):
    """
    Accepts live video frames from webcam or mobile devices,
    runs full facial recognition, dress code + ID card verification, and returns real analysis.
    """
    str_id = str(camera_id)
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None or frame.size == 0:
        raise HTTPException(
            status_code=400, detail="Invalid image payload received from device"
        )

    # Store frame in frame cache
    mobile_uploaded_frames[str_id] = {
        "frame": frame,
        "timestamp": time.time(),
    }

    # Get camera settings (assigned function & environment)
    assigned_function = "FACE_ATTENDANCE"
    environment_id = 1
    try:
        conn = get_db_connection()
        row = conn.execute(
            "SELECT environment_id, assigned_function FROM cameras WHERE id = ?",
            (str_id,),
        ).fetchone()
        if row:
            if row["assigned_function"]:
                assigned_function = row["assigned_function"]
            if row["environment_id"]:
                environment_id = row["environment_id"]
        conn.close()
    except Exception:
        pass

    # Run Real Face Recognition & Perception
    from api.face_recognition_service import analyze_surveillance_frame

    analysis = analyze_surveillance_frame(
        frame=frame,
        environment_id=environment_id,
        assigned_function=assigned_function,
    )

    now_ts = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # PILLAR 1: Face Attendance (Auto-mark present for enrolled identities)
    if analysis.get("is_match") and analysis.get("matched_person"):
        p_id = analysis["matched_person"]["id"]
        try:
            conn = get_db_connection()
            today_str = datetime.now().strftime("%Y-%m-%d")
            existing = conn.execute(
                "SELECT id FROM attendance_records WHERE person_id = ? AND timestamp LIKE ?",
                (p_id, f"{today_str}%"),
            ).fetchone()
            if not existing:
                status = "LATE" if datetime.now().hour >= 9 else "PRESENT"
                conn.execute(
                    """
                    INSERT INTO attendance_records (person_id, camera_id, environment_id, timestamp, confidence, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p_id,
                        int(camera_id) if camera_id.isdigit() else 1,
                        environment_id,
                        now_str,
                        analysis["similarity"],
                        status,
                    ),
                )
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"[CameraStream] Attendance recording error: {e}")

    # PILLAR 2: Dress Code & ID Card Compliance (Evaluated for EVERY person: enrolled or unenrolled)
    dress = analysis.get("dress_code")
    if dress:
        is_dress_pass = dress.get("dress_compliant", True)
        has_id = dress.get("id_card_detected", False)
        dress_type = dress.get("dress_type", "Regular Formals")

        # Log alert if wearing casual attire or ID card is missing
        if not is_dress_pass or not has_id:
            person_name = (
                analysis["matched_person"]["name"]
                if analysis.get("is_match") and analysis.get("matched_person")
                else f"Unenrolled {analysis.get('detected_gender', 'Individual').capitalize()}"
            )
            cooldown_key = f"dress_{camera_id}_{person_name}"
            if now_ts - stream_alert_cooldown.get(cooldown_key, 0) > 25:
                stream_alert_cooldown[cooldown_key] = now_ts
                try:
                    conn = get_db_connection()
                    reasons = []
                    if not is_dress_pass:
                        reasons.append(f"Casual Attire ({dress_type})")
                    if not has_id:
                        reasons.append("Missing ID Card")
                    violation_detail = " & ".join(reasons)
                    priority = (
                        "HIGH" if (not is_dress_pass and not has_id) else "MEDIUM"
                    )

                    conn.execute(
                        """
                        INSERT INTO alerts (timestamp, object, priority, confidence, status, camera_id)
                        VALUES (?, ?, ?, 0.92, 'ACTIVE', ?)
                        """,
                        (
                            now_str,
                            f"DRESS CODE VIOLATION: {person_name} — {violation_detail} detected",
                            priority,
                            str(camera_id),
                        ),
                    )
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[CameraStream] Dress alert error: {e}")

    # PILLAR 3: Security & Prohibited Activities (Smartphones, Cheating, Weapons)
    prohibited = analysis.get("prohibited_items", [])
    if prohibited:
        item = prohibited[0].upper()
        sec_key = f"sec_{camera_id}_{item}"
        if now_ts - stream_alert_cooldown.get(sec_key, 0) > 25:
            stream_alert_cooldown[sec_key] = now_ts
            try:
                conn = get_db_connection()
                conn.execute(
                    """
                    INSERT INTO alerts (timestamp, object, priority, confidence, status, camera_id)
                    VALUES (?, ?, 'CRITICAL', 0.96, 'ACTIVE', ?)
                    """,
                    (
                        now_str,
                        f"CRITICAL SECURITY ALERT: PROHIBITED {item} DETECTED IN CAMERA FEED",
                        str(camera_id),
                    ),
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[CameraStream] Security alert error: {e}")

    # Ensure worker thread is initialized
    get_camera(str_id)

    return {
        "success": True,
        "message": f"Frame analyzed for Camera {camera_id}",
        "dimensions": f"{frame.shape[1]}x{frame.shape[0]}",
        "analysis": analysis,
    }


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
                    "is_live_hardware": camera_instances.get(cid) is not None,
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
    is_hardware = camera_instances.get(str_id) is not None
    has_mobile_stream = (
        str_id in mobile_uploaded_frames
        and (time.time() - mobile_uploaded_frames[str_id]["timestamp"]) < 10.0
    )

    return {
        "success": True,
        "camera_id": camera_id,
        "active": active,
        "frame_available": frame_available,
        "is_hardware": is_hardware,
        "has_mobile_stream": has_mobile_stream,
    }
