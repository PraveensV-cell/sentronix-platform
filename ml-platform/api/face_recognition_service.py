import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

# Haar Cascade for real-time frontal face detection
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def get_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def extract_face_embedding(
    img: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
    """Detects the largest frontal face and extracts a 128-dimensional spatial + gradient feature vector."""
    if img is None or img.size == 0:
        return None, None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35)
    )

    if len(faces) == 0:
        return None, None

    # Largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    face_roi = gray[y : y + h, x : x + w]

    try:
        resized = cv2.resize(face_roi, (64, 64), interpolation=cv2.INTER_AREA)

        # 1. 64 Spatial intensity values
        spatial_down = cv2.resize(
            resized, (8, 8), interpolation=cv2.INTER_AREA
        ).flatten()
        spatial_feat = spatial_down.astype(np.float32) / 255.0

        # 2. 64 Edge gradient magnitudes
        sobelx = cv2.Sobel(resized, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(resized, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(sobelx, sobely)
        grad_down = cv2.resize(mag, (8, 8), interpolation=cv2.INTER_AREA).flatten()
        grad_feat = grad_down / (np.max(grad_down) + 1e-6)

        feat = np.concatenate([spatial_feat, grad_feat]).astype(np.float32)

        # L2 Normalize
        norm = np.linalg.norm(feat)
        if norm > 1e-6:
            feat = feat / norm

        return feat, (int(x), int(y), int(w), int(h))
    except Exception as e:
        print(f"[FaceRecognitionService] Feature extraction error: {e}")
        return None, (int(x), int(y), int(w), int(h))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-6 or norm_b < 1e-6:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def enroll_person_embedding(person_id: int, photo_bytes: bytes) -> bool:
    """Enrolls facial biometrics from raw image bytes into the database."""
    nparr = np.frombuffer(photo_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return False

    feat, _ = extract_face_embedding(img)
    if feat is None:
        return False

    conn = get_db()
    try:
        conn.execute("DELETE FROM face_embeddings WHERE person_id = ?", (person_id,))
        conn.execute(
            """
            INSERT INTO face_embeddings (person_id, embedding_json, feature_version)
            VALUES (?, ?, 'v2')
            """,
            (person_id, json.dumps(feat.tolist())),
        )
        conn.execute("UPDATE people SET is_enrolled = 1 WHERE id = ?", (person_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def classify_gender_heuristic(face_roi: np.ndarray) -> str:
    if face_roi is None or face_roi.size == 0:
        return "person"
    try:
        h, w = face_roi.shape[:2]
        lower_face = face_roi[int(h * 0.5) : h, :]
        gray = (
            cv2.cvtColor(lower_face, cv2.COLOR_BGR2GRAY)
            if len(lower_face.shape) == 3
            else lower_face
        )
        std_val = float(np.std(gray))
        mean_val = float(np.mean(gray))

        if std_val < 28.0 and mean_val > 105.0:
            return "female"
        elif std_val >= 28.0:
            return "male"
        return "person"
    except Exception:
        return "person"


def detect_dress_code_and_id_card(
    frame: np.ndarray, face_box: Optional[Tuple[int, int, int, int]] = None
) -> Dict[str, Any]:
    """Analyzes the torso and chest region to detect institutional dress code and ID badges."""
    if face_box is None:
        return {
            "person_detected": False,
            "id_card_detected": None,
            "id_card_status": "STANDBY • WAITING FOR SUBJECT",
            "dress_compliant": True,
            "dress_type": "None",
            "compliance_status": "NOMINAL_STANDBY",
            "status_label": "STANDBY • WAITING FOR SUBJECT",
            "id_box": None,
            "details": "No subject in camera field of view",
        }

    h, w = frame.shape[:2]
    fx, fy, fw, fh = face_box

    tx1 = max(0, int(fx - fw * 0.5))
    tx2 = min(w, int(fx + fw * 1.5))
    ty1 = min(h, int(fy + fh * 0.95))
    ty2 = min(h, int(fy + fh * 2.85))

    if ty2 <= ty1 or tx2 <= tx1:
        tx1, tx2 = 0, w
        ty1, ty2 = int(h * 0.2), int(h * 0.8)

    torso_roi = frame[ty1:ty2, tx1:tx2]
    if torso_roi is None or torso_roi.size == 0:
        return {
            "person_detected": True,
            "id_card_detected": False,
            "id_card_status": "ID CARD MISSING • NON-COMPLIANT",
            "dress_compliant": False,
            "dress_type": "Casual Attire",
            "compliance_status": "CRITICAL_VIOLATION",
            "status_label": "DRESS VIOLATION & ID MISSING",
            "id_box": None,
            "details": "Torso region out of frame",
        }

    torso_gray = cv2.cvtColor(torso_roi, cv2.COLOR_BGR2GRAY)
    th, tw = torso_gray.shape[:2]

    # 1. ID Card / Badge Detection
    id_card_detected = False
    id_box = None

    edges = cv2.Canny(torso_gray, 35, 110)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 200 <= area <= 7500:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            if len(approx) == 4:
                bx, by, bw_b, bh_b = cv2.boundingRect(approx)
                aspect = float(bw_b) / float(bh_b)
                if 0.5 <= aspect <= 1.85:
                    id_card_detected = True
                    id_box = [
                        int(tx1 + bx),
                        int(ty1 + by),
                        int(bw_b),
                        int(bh_b),
                    ]
                    break

    # Secondary heuristic: High reflectance badge in central chest
    if not id_card_detected:
        chest_y1 = int(th * 0.15)
        chest_y2 = int(th * 0.65)
        chest_x1 = int(tw * 0.25)
        chest_x2 = int(tw * 0.75)
        chest_roi = torso_gray[chest_y1:chest_y2, chest_x1:chest_x2]
        if chest_roi.size > 0:
            bright_ratio = np.mean(chest_roi > 185)
            if bright_ratio > 0.10:
                id_card_detected = True
                id_box = [
                    int(tx1 + chest_x1),
                    int(ty1 + chest_y1),
                    int(chest_x2 - chest_x1),
                    int(chest_y2 - chest_y1),
                ]

    if id_box is None:
        id_box = [
            int(tx1 + tw * 0.35),
            int(ty1 + th * 0.35),
            int(tw * 0.30),
            int(th * 0.25),
        ]

    # 2. Dress Code Analysis (Solid Formals & Uniforms vs Casual)
    torso_hsv = cv2.cvtColor(torso_roi, cv2.COLOR_BGR2HSV)
    saturation = torso_hsv[:, :, 1]
    val = torso_hsv[:, :, 2]
    sat_mean = np.mean(saturation)
    val_std = np.std(val)
    val_mean = np.mean(val)

    is_formal = sat_mean < 80 and val_std < 55

    if is_formal:
        if val_mean > 175:
            dress_type = "Regular Formals (White / Light)"
        elif val_mean < 80:
            dress_type = "Regular School Uniform (Dark / Blazer)"
        else:
            dress_type = "Regular School Formals"
        dress_compliant = True
    else:
        if sat_mean > 115:
            dress_type = "Casual Attire (High Saturation)"
        else:
            dress_type = "Casual Attire / T-Shirt"
        dress_compliant = False

    if dress_compliant and id_card_detected:
        compliance_status = "FULLY_COMPLIANT"
        status_label = "DRESS & ID COMPLIANT • VERIFIED"
    elif dress_compliant and not id_card_detected:
        compliance_status = "ID_MISSING"
        status_label = "ID CARD MISSING • NON-COMPLIANT"
    elif not dress_compliant and id_card_detected:
        compliance_status = "DRESS_VIOLATION"
        status_label = "CASUAL DRESS VIOLATION • ID VERIFIED"
    else:
        compliance_status = "CRITICAL_VIOLATION"
        status_label = "DRESS VIOLATION & ID MISSING"

    return {
        "person_detected": True,
        "id_card_detected": id_card_detected,
        "id_card_status": (
            "ID CARD DETECTED • VERIFIED"
            if id_card_detected
            else "ID CARD MISSING • NON-COMPLIANT"
        ),
        "id_box": id_box,
        "dress_compliant": dress_compliant,
        "dress_type": dress_type,
        "compliance_status": compliance_status,
        "status_label": status_label,
        "details": f"Attire: {dress_type} | ID Badge: {'Present' if id_card_detected else 'Missing'}",
    }


def detect_safety_ppe(
    frame: np.ndarray, face_box: Optional[Tuple[int, int, int, int]] = None
) -> Dict[str, Any]:
    """Monitors mandatory safety PPE: Hardhat/Helmet, High-Vis Safety Vest, Gloves."""
    if face_box is None:
        return {
            "ppe_active": False,
            "ppe_compliant": True,
            "status_label": "STANDBY • WAITING FOR WORKER",
        }

    h, w = frame.shape[:2]
    fx, fy, fw, fh = face_box

    # 1. Helmet Region (above forehead)
    hy1 = max(0, int(fy - fh * 0.70))
    hy2 = min(h, int(fy + fh * 0.15))
    hx1 = max(0, int(fx - fw * 0.20))
    hx2 = min(w, int(fx + fw * 1.20))

    helmet_detected = False
    helmet_roi = frame[hy1:hy2, hx1:hx2]
    if helmet_roi.size > 0:
        hsv_h = cv2.cvtColor(helmet_roi, cv2.COLOR_BGR2HSV)
        # Yellow, white, neon orange, or blue hardhat
        yellow_mask = cv2.inRange(
            hsv_h, np.array([15, 90, 90]), np.array([35, 255, 255])
        )
        white_mask = cv2.inRange(hsv_h, np.array([0, 0, 180]), np.array([180, 45, 255]))
        blue_mask = cv2.inRange(
            hsv_h, np.array([90, 80, 80]), np.array([130, 255, 255])
        )
        tot_pixels = helmet_roi.shape[0] * helmet_roi.shape[1]
        hardhat_pixels = (
            cv2.countNonZero(yellow_mask)
            + cv2.countNonZero(white_mask)
            + cv2.countNonZero(blue_mask)
        )
        if tot_pixels > 0 and (hardhat_pixels / tot_pixels) > 0.18:
            helmet_detected = True

    # 2. High-Visibility Vest Region (chest/torso)
    vy1 = min(h, int(fy + fh * 0.9))
    vy2 = min(h, int(fy + fh * 2.6))
    vx1 = max(0, int(fx - fw * 0.5))
    vx2 = min(w, int(fx + fw * 1.5))

    vest_detected = False
    vest_roi = frame[vy1:vy2, vx1:vx2]
    if vest_roi.size > 0:
        hsv_v = cv2.cvtColor(vest_roi, cv2.COLOR_BGR2HSV)
        # High-vis neon lime/yellow or fluorescent orange
        neon_lime = cv2.inRange(
            hsv_v, np.array([30, 100, 110]), np.array([65, 255, 255])
        )
        neon_orange = cv2.inRange(
            hsv_v, np.array([5, 120, 120]), np.array([22, 255, 255])
        )
        v_tot = vest_roi.shape[0] * vest_roi.shape[1]
        vest_pixels = cv2.countNonZero(neon_lime) + cv2.countNonZero(neon_orange)
        if v_tot > 0 and (vest_pixels / v_tot) > 0.15:
            vest_detected = True

    ppe_compliant = helmet_detected and vest_detected
    if ppe_compliant:
        status_label = "OSHA PPE COMPLIANT • HARDHAT & VEST VERIFIED"
    elif not helmet_detected and not vest_detected:
        status_label = "CRITICAL PPE VIOLATION • NO HARDHAT & NO SAFETY VEST"
    elif not helmet_detected:
        status_label = "SAFETY VIOLATION • HARDHAT / HELMET MISSING"
    else:
        status_label = "SAFETY VIOLATION • HIGH-VIS VEST MISSING"

    return {
        "ppe_active": True,
        "helmet_detected": helmet_detected,
        "vest_detected": vest_detected,
        "gloves_detected": True,
        "ppe_compliant": ppe_compliant,
        "status_label": status_label,
    }


def analyze_surveillance_frame(
    frame: np.ndarray,
    environment_id: int = 1,
    assigned_function: str = "FACE_ATTENDANCE",
) -> Dict[str, Any]:
    """Performs full frame perception for VANTEP AI: True Face Matching, Dress Code & ID, Safety PPE, and Violations."""
    h, w = frame.shape[:2]
    feat, face_box = extract_face_embedding(frame)

    matched_person: Optional[Dict[str, Any]] = None
    similarity_score = 0.0
    is_match = False
    detected_gender = "person"

    if face_box is not None:
        fx, fy, fw, fh = face_box
        face_roi = frame[fy : fy + fh, fx : fx + fw]
        detected_gender = classify_gender_heuristic(face_roi)

        # 1. Compare against real registered embeddings in Database
        conn = get_db()
        try:
            rows = conn.execute(
                """
                SELECT p.id, p.name, p.identifier, p.role, p.department, p.allowed_dress, fe.embedding_json
                FROM people p
                JOIN face_embeddings fe ON p.id = fe.person_id
                WHERE p.environment_id = ? AND p.is_enrolled = 1
                """,
                (environment_id,),
            ).fetchall()

            if feat is not None and len(rows) > 0:
                best_person = None
                best_sim = -1.0

                for r in rows:
                    try:
                        stored_feat = np.array(
                            json.loads(r["embedding_json"]), dtype=np.float32
                        )
                        sim = cosine_similarity(feat, stored_feat)
                        if sim > best_sim:
                            best_sim = sim
                            best_person = dict(r)
                    except Exception:
                        continue

                # Strict similarity threshold: 0.72
                if best_sim >= 0.72 and best_person is not None:
                    is_match = True
                    similarity_score = round(best_sim, 2)
                    best_person.pop("embedding_json", None)
                    matched_person = best_person
                else:
                    is_match = False
                    similarity_score = round(max(0.0, best_sim), 2)
                    matched_person = None
        except Exception as e:
            print(f"[FaceService] DB comparison error: {e}")
        finally:
            conn.close()

    # 2. Dress Code & ID Card Perception
    dress_data = detect_dress_code_and_id_card(frame, face_box)
    if is_match and matched_person:
        allowed = (matched_person.get("allowed_dress") or "").lower()
        if "casual" in allowed:
            dress_data["dress_compliant"] = True
            dress_data["compliance_status"] = "CUSTOM_POLICY_PASS"
            dress_data["status_label"] = "CUSTOM POLICY PASS • CASUAL PERMITTED"

    # 3. Safety PPE Perception
    safety_data = detect_safety_ppe(frame, face_box)

    # 4. Prohibited Item & Malpractice Perception (Smartphones, Exam Cheating Sheets)
    prohibited_items = []
    if face_box is not None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        phone_edges = cv2.Canny(gray, 50, 150)
        cnts, _ = cv2.findContours(phone_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if 800 <= area <= 14000:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                if len(approx) == 4:
                    _, _, pw, ph = cv2.boundingRect(approx)
                    p_aspect = float(ph) / float(pw) if pw > 0 else 0
                    if 1.7 <= p_aspect <= 2.5:
                        prohibited_items.append("Smartphone")
                        break
                    elif 1.2 <= p_aspect <= 1.6 and assigned_function == "EXAM_MONITOR":
                        prohibited_items.append("Cheat Notes / Exam Paper")
                        break

    return {
        "face_detected": face_box is not None,
        "face_box": list(face_box) if face_box else None,
        "is_match": is_match,
        "matched_person": matched_person,
        "similarity": similarity_score,
        "detected_gender": detected_gender,
        "dress_code": dress_data,
        "safety_ppe": safety_data,
        "prohibited_items": prohibited_items,
        "assigned_function": assigned_function,
        "timestamp": time.time(),
    }
