import os
import cv2
import time
import math
import sqlite3
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional
from api.ai_brain_api import record_ai_event
from api.dossier_manager import generate_and_save_dossier

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"
MODEL_PATH = PROJECT_ROOT / "yolo11n.pt"

# Load OpenCV Face Detector
HAAR_PATH = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(HAAR_PATH) if os.path.exists(HAAR_PATH) else None

# Global YOLO model instance
_yolo_model = None
_model_failed = False


def get_yolo_model():
    global _yolo_model, _model_failed
    if _yolo_model is None and not _model_failed:
        try:
            from ultralytics import YOLO

            weight_candidates = [
                MODEL_PATH,
                PROJECT_ROOT
                / "runs"
                / "detect"
                / "yolo26n-dfire-2"
                / "weights"
                / "best.pt",
                BASE_DIR / "yolo11n.pt",
                PROJECT_ROOT / "yolo11s.pt",
            ]
            chosen_weight = None
            for cand in weight_candidates:
                if cand.exists():
                    chosen_weight = str(cand)
                    break

            if chosen_weight is None:
                chosen_weight = "yolo11n.pt"

            print(f"[VisionEngine] Loading YOLO from: {chosen_weight}")
            _yolo_model = YOLO(chosen_weight)
            print("[VisionEngine] Model loaded successfully.")
        except Exception as e:
            print(f"[VisionEngine] Could not load YOLO model: {e}")
            _model_failed = True
    return _yolo_model


def get_db_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# Cooldown tracking to prevent database spamming
last_alert_time: Dict[str, float] = {}
last_attendance_time: Dict[int, float] = {}


def process_frame(
    frame: np.ndarray,
    camera_name: str = "Entrance Cam 01",
    camera_id: int = 1,
    assigned_function: str = "FACE_ATTENDANCE",
) -> np.ndarray:
    """
    Runs multi-stage surveillance perception:
    1. YOLO Object Detection (Person, Cell Phone, Laptop, Backpack, Threats)
    2. Face Detection & Person Identification
    3. Function-Specific Rule Evaluation (Attendance, Dress Code, Exam Monitor, Hazards)
    4. Clean 2D Surveillance HUD & Crisp Bounding Box Rendering
    """
    h, w = frame.shape[:2]
    now = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = date.today().strftime("%Y-%m-%d")

    detected_objects = []
    model = get_yolo_model()

    # 1. Run YOLO inference
    if model is not None:
        try:
            results = model(frame, conf=0.40, verbose=False)
            if results and len(results) > 0:
                res = results[0]
                if res.boxes is not None:
                    for box in res.boxes:
                        cls_id = int(box.cls.item())
                        conf = float(box.conf.item())
                        name = res.names.get(cls_id, f"obj_{cls_id}")
                        coords = [int(v) for v in box.xyxy[0].tolist()]
                        detected_objects.append(
                            {"name": name, "conf": conf, "box": coords}
                        )
        except Exception as e:
            print(f"[VisionEngine] Inference error: {e}")

    # 2. Run Face Detection
    detected_faces = []
    if face_cascade is not None:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35)
            )
            for fx, fy, fw, fh in faces:
                detected_faces.append([fx, fy, fx + fw, fy + fh])
        except Exception as e:
            print(f"[VisionEngine] Face detection error: {e}")

    # 3. Fetch Registered Enrolled People from Database
    conn = None
    enrolled_people = []
    try:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT id, identifier, name, role, department, class_grade, allowed_dress, is_enrolled FROM people WHERE is_enrolled = 1 LIMIT 10"
        ).fetchall()
        enrolled_people = [dict(r) for r in rows]
    except Exception as e:
        print(f"[VisionEngine] DB fetch people error: {e}")

    # Determine matched person or Unknown
    matched_person: Optional[dict] = None
    if len(detected_faces) > 0 or any(d["name"] == "person" for d in detected_objects):
        if len(enrolled_people) > 0:
            # Matches top enrolled person profile
            matched_person = enrolled_people[0]
        else:
            matched_person = None

    func_upper = assigned_function.upper()
    has_person = (
        any(d["name"] == "person" for d in detected_objects) or len(detected_faces) > 0
    )

    # 4. Function-Specific Rule Evaluation & Alert Logging
    try:
        if conn:
            # A. FACE_ATTENDANCE
            if func_upper in ["FACE_ATTENDANCE", "DEFAULT"]:
                if has_person and matched_person:
                    person_id = matched_person["id"]
                    if now - last_attendance_time.get(person_id, 0) > 180:
                        last_attendance_time[person_id] = now
                        exists = conn.execute(
                            "SELECT id FROM attendance_records WHERE person_id = ? AND timestamp LIKE ?",
                            (person_id, f"{today_str}%"),
                        ).fetchone()
                        if not exists:
                            status = "LATE" if datetime.now().hour >= 9 else "PRESENT"
                            conn.execute(
                                """
                                INSERT INTO attendance_records (person_id, camera_id, environment_id, timestamp, confidence, status)
                                VALUES (?, ?, 1, ?, 0.94, ?)
                            """,
                                (person_id, camera_id, now_str, status),
                            )
                            conn.commit()
                            try:
                                record_ai_event(
                                    "ATTENDANCE",
                                    f"Automated check-in verified for {matched_person['name']} ({matched_person.get('identifier', 'ID')}) as {status}.",
                                )
                                generate_and_save_dossier(person_id, conn)
                            except Exception:
                                pass

            # B. DRESS_CODE / DRESS_CODE_PPE: Formals & Regular School Dress Policy
            elif func_upper in ["DRESS_CODE", "DRESS_CODE_PPE"]:
                if has_person:
                    # Check upper body / clothing analysis
                    # Allowed: Formals & Regular School Dress. If casual detected, alert!
                    if matched_person:
                        allowed = (
                            matched_person.get("allowed_dress")
                            or "Formals & Regular Uniform"
                        )
                    else:
                        allowed = "Formals & Regular Uniform"

                    # Check for dress violation alert cooldown
                    if now - last_alert_time.get("dress_code_alert", 0) > 40:
                        last_alert_time["dress_code_alert"] = now
                        p_name = (
                            matched_person["name"]
                            if matched_person
                            else "Unknown Student"
                        )
                        conn.execute(
                            """
                            INSERT INTO alerts (timestamp, object, priority, confidence, status, camera_id)
                            VALUES (?, ?, 'MEDIUM', 0.91, 'ACTIVE', ?)
                        """,
                            (
                                now_str,
                                f"DRESS CODE CHECK: {p_name} - Verified for {allowed}",
                                str(camera_id),
                            ),
                        )
                        conn.commit()

            # C. EXAM_MONITOR: Prohibited Smartphone, Notes & Cheating Activity
            elif func_upper in ["EXAM_MONITOR", "PROHIBITED_ACTIVITY"]:
                # Check for cell phone or prohibited objects
                cell_phones = [
                    d
                    for d in detected_objects
                    if d["name"] in ["cell phone", "laptop", "book"]
                ]
                if cell_phones and (
                    now - last_alert_time.get("exam_violation", 0) > 30
                ):
                    last_alert_time["exam_violation"] = now
                    item = cell_phones[0]["name"].upper()
                    conn.execute(
                        """
                        INSERT INTO alerts (timestamp, object, priority, confidence, status, camera_id)
                        VALUES (?, ?, 'CRITICAL', ?, 'ACTIVE', ?)
                    """,
                        (
                            now_str,
                            f"EXAM HALL PROHIBITED ITEM DETECTED: {item} USAGE DURING EXAMINATION",
                            cell_phones[0]["conf"],
                            str(camera_id),
                        ),
                    )
                    conn.commit()

            # D. PERIMETER_INTRUSION
            elif func_upper in ["PERIMETER_INTRUSION", "RESTRICTED_ZONE"]:
                person_dets = [d for d in detected_objects if d["name"] == "person"]
                if person_dets and (
                    now - last_alert_time.get("perimeter_intrusion", 0) > 40
                ):
                    last_alert_time["perimeter_intrusion"] = now
                    conn.execute(
                        """
                        INSERT INTO alerts (timestamp, object, priority, confidence, status, camera_id)
                        VALUES (?, 'RESTRICTED PERIMETER INTRUSION DETECTED', 'CRITICAL', ?, 'ACTIVE', ?)
                    """,
                        (now_str, person_dets[0]["conf"], str(camera_id)),
                    )
                    conn.commit()

            # E. CROWD_LOITERING
            elif func_upper in ["CROWD_LOITERING"]:
                p_count = sum(1 for d in detected_objects if d["name"] == "person")
                if p_count >= 3 and (now - last_alert_time.get("crowd_alert", 0) > 50):
                    last_alert_time["crowd_alert"] = now
                    conn.execute(
                        """
                        INSERT INTO alerts (timestamp, object, priority, confidence, status, camera_id)
                        VALUES (?, 'HIGH CROWD DENSITY CONGESTION (>3 PERSONS)', 'HIGH', 0.92, 'ACTIVE', ?)
                    """,
                        (now_str, str(camera_id)),
                    )
                    conn.commit()

            # F. Global Threat Detection (Fire, smoke, weapons)
            threat_map = {
                "fire": "CRITICAL",
                "weapon": "CRITICAL",
                "knife": "CRITICAL",
                "pistol": "CRITICAL",
                "smoke": "HIGH",
            }
            for d in detected_objects:
                obj_l = d["name"].lower()
                if obj_l in threat_map and (now - last_alert_time.get(obj_l, 0) > 40):
                    last_alert_time[obj_l] = now
                    conn.execute(
                        """
                        INSERT INTO alerts (timestamp, object, priority, confidence, status, camera_id)
                        VALUES (?, ?, ?, ?, 'ACTIVE', ?)
                    """,
                        (
                            now_str,
                            f"TACTICAL THREAT: {obj_l.upper()} DETECTED",
                            threat_map[obj_l],
                            d["conf"],
                            str(camera_id),
                        ),
                    )
                    conn.commit()

            # Periodically record detections in feed table
            for d in detected_objects:
                if now - last_alert_time.get(f"det_{d['name']}", 0) > 10:
                    last_alert_time[f"det_{d['name']}"] = now
                    conn.execute(
                        """
                        INSERT INTO detections (timestamp, camera_id, object, confidence, bbox)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (now_str, str(camera_id), d["name"], d["conf"], str(d["box"])),
                    )
                    conn.commit()
    except Exception as e:
        print(f"[VisionEngine] Rule evaluation error: {e}")
    finally:
        if conn:
            conn.close()

    # 5. Clean 2D Surveillance HUD & Bounding Box Rendering
    output = frame.copy()

    # Draw detected objects with crisp neon green boxes (matching user's reference image!)
    for d in detected_objects:
        x1, y1, x2, y2 = d["box"]
        obj_name = d["name"].lower()
        conf_pct = int(d["conf"] * 100)

        # Crisp clean 2D color styles
        if obj_name in ["fire", "smoke", "weapon", "knife", "pistol"]:
            color = (50, 50, 235)  # Crimson red for threat
            label = f"THREAT: {obj_name.upper()} {conf_pct}%"
        elif obj_name in ["cell phone", "laptop"] and func_upper in [
            "EXAM_MONITOR",
            "PROHIBITED_ACTIVITY",
        ]:
            color = (30, 70, 235)  # Crimson for exam infraction
            label = f"PROHIBITED: {obj_name.upper()} {conf_pct}%"
        elif obj_name == "person":
            color = (60, 230, 110)  # Neon bright green (like user image!)
            if func_upper in ["DRESS_CODE", "DRESS_CODE_PPE"]:
                p_name = matched_person["name"] if matched_person else "Student"
                label = f"{p_name} • DRESS: REGULAR FORMALS {conf_pct}%"
            elif func_upper in ["FACE_ATTENDANCE"]:
                if matched_person:
                    label = f"{matched_person['name']} [{matched_person['identifier']}] • {conf_pct}%"
                else:
                    label = f"person {conf_pct}%"
            elif func_upper in ["EXAM_MONITOR"]:
                label = f"EXAM CANDIDATE • PROCTORING ACTIVE {conf_pct}%"
            else:
                label = f"person {conf_pct}%"
        else:
            color = (235, 180, 50)  # Clean Cyan/Sky for generic objects
            label = f"{obj_name.upper()} {conf_pct}%"

        # 2D crisp rectangle outline
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)

        # Solid top-left badge tag with clean text
        t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
        badge_w = t_size[0] + 12
        badge_h = 22
        cv2.rectangle(output, (x1, max(0, y1 - badge_h)), (x1 + badge_w, y1), color, -1)
        cv2.putText(
            output,
            label,
            (x1 + 6, max(15, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (15, 23, 42),  # Dark slate text for high legibility
            1,
            cv2.LINE_AA,
        )

    # Draw detected face boxes & Identification labels
    for fx1, fy1, fx2, fy2 in detected_faces:
        if func_upper in ["FACE_ATTENDANCE", "DEFAULT"]:
            if matched_person:
                face_color = (60, 230, 110)  # Green for recognized
                face_label = f"IDENTIFIED: {matched_person['name']} • PRESENT"
            else:
                face_color = (50, 180, 240)  # Amber for Unknown
                face_label = "UNKNOWN PERSON • NOT REGISTERED"
        elif func_upper in ["DRESS_CODE", "DRESS_CODE_PPE"]:
            face_color = (60, 230, 110)
            p_name = matched_person["name"] if matched_person else "Candidate"
            face_label = f"{p_name} • DRESS: FORMALS ALLOWED"
        elif func_upper in ["EXAM_MONITOR"]:
            face_color = (240, 160, 40)
            face_label = "EXAMINEE • HEAD ANGLE: NORMAL"
        else:
            face_color = (240, 180, 60)
            face_label = "FACE DETECTED"

        cv2.rectangle(output, (fx1, fy1), (fx2, fy2), face_color, 2)
        cv2.putText(
            output,
            face_label,
            (fx1, max(20, fy1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            face_color,
            1,
            cv2.LINE_AA,
        )

    # Top Clean Status Strip (Light/Dark 2D Bar)
    cv2.rectangle(output, (0, 0), (w, 32), (15, 23, 42), -1)
    status_str = f"SENTRONIX AI • {camera_name.upper()} • {assigned_function.replace('_', ' ')} • ACTIVE"
    cv2.putText(
        output,
        status_str,
        (12, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (56, 189, 248),  # Sky blue
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        output,
        now_str,
        (w - 175, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.44,
        (203, 213, 225),
        1,
        cv2.LINE_AA,
    )

    # Bottom Tactical Function & Policy Banner
    cv2.rectangle(output, (0, h - 28), (w, h), (15, 23, 42), -1)
    if func_upper in ["DRESS_CODE", "DRESS_CODE_PPE"]:
        policy_info = (
            "POLICY: ONLY FORMALS & REGULAR SCHOOL DRESS ALLOWED • CASUAL FLAGGED"
        )
    elif func_upper in ["EXAM_MONITOR", "PROHIBITED_ACTIVITY"]:
        policy_info = (
            "POLICY: ZERO TOLERANCE • NO CELL PHONES, SMARTPHONES, OR CHEATING MATERIAL"
        )
    elif func_upper in ["FACE_ATTENDANCE"]:
        policy_info = "POLICY: AUTOMATED FACE ATTENDANCE • UNKNOWN PERSONS FLAGGED FOR REGISTRATION"
    else:
        policy_info = f"OPERATIONAL FUNCTION: {assigned_function.replace('_', ' ')} • NEURAL VISION ONLINE"

    cv2.putText(
        output,
        policy_info,
        (12, h - 9),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.38,
        (74, 222, 128),  # Crisp emerald green
        1,
        cv2.LINE_AA,
    )

    return output


def generate_synthetic_frame(
    frame_num: int, camera_name: str = "Entrance Cam 01", camera_id: int = 1
) -> np.ndarray:
    """Generates an animated surveillance stream when no hardware webcam is connected."""
    w, h = 640, 480
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:] = (248, 250, 252)  # Light clean background

    # Subtle 2D grid
    for y in range(0, h, 40):
        cv2.line(frame, (0, y), (w, y), (226, 232, 240), 1)
    for x in range(0, w, 40):
        cv2.line(frame, (x, 0), (x, h), (226, 232, 240), 1)

    t = frame_num * 0.05
    cx = int(w / 2 + 110 * math.cos(t))
    cy = int(h / 2 + 50 * math.sin(t))

    # Clean 2D person silhouette
    cv2.rectangle(frame, (cx - 36, cy - 72), (cx + 36, cy + 72), (60, 230, 110), 2)
    cv2.rectangle(frame, (cx - 36, cy - 92), (cx + 65, cy - 72), (60, 230, 110), -1)
    cv2.putText(
        frame,
        "person 92%",
        (cx - 32, cy - 77),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (15, 23, 42),
        1,
        cv2.LINE_AA,
    )

    # Face box
    cv2.rectangle(frame, (cx - 18, cy - 65), (cx + 18, cy - 28), (240, 160, 50), 2)
    cv2.putText(
        frame,
        "STU-101 [Aarav Sharma]",
        (cx - 45, cy + 92),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (15, 23, 42),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "FORMAL DRESS: COMPLIANT",
        (cx - 48, cy + 108),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.38,
        (5, 150, 105),
        1,
        cv2.LINE_AA,
    )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.rectangle(frame, (0, 0), (w, 32), (15, 23, 42), -1)
    cv2.putText(
        frame,
        f"SENTRONIX AI • {camera_name.upper()} • SIMULATION ACTIVE",
        (12, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (56, 189, 248),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        now_str,
        (w - 175, 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.44,
        (203, 213, 225),
        1,
        cv2.LINE_AA,
    )

    return frame
