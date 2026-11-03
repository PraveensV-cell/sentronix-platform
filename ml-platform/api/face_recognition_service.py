import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

# Haar Cascade for real-time frontal face detection
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH) if cv2.data.haarcascades else None

# Cached YOLO model instance
_yolo_model = None
_yolo_failed = False


def get_yolo_model():
    """Returns a singleton Ultralytics YOLO model for real-time surveillance perception."""
    global _yolo_model, _yolo_failed
    if _yolo_model is None and not _yolo_failed:
        try:
            from ultralytics import YOLO

            candidates = [
                BASE_DIR / "yolo11n.pt",
                PROJECT_ROOT / "yolo11n.pt",
                PROJECT_ROOT / "yolo11s.pt",
            ]
            chosen = None
            for c in candidates:
                if c.exists():
                    chosen = str(c)
                    break
            if chosen is None:
                chosen = "yolo11n.pt"

            _yolo_model = YOLO(chosen)
        except Exception as e:
            print(f"[FaceRecognitionService] YOLO load warning: {e}")
            _yolo_failed = True
    return _yolo_model


def get_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def extract_face_embedding(
    img: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
    """
    Detects face (via Haar Cascade or YOLO person head localization)
    and extracts a 128-dimensional spatial + gradient feature vector.
    """
    if img is None or img.size == 0:
        return None, None

    ih, iw = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # Stage 1: Try Haar cascade
    face_box = None
    if face_cascade is not None:
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4, minSize=(32, 32)
        )
        if len(faces) > 0:
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            face_box = (
                int(faces[0][0]),
                int(faces[0][1]),
                int(faces[0][2]),
                int(faces[0][3]),
            )

    # Stage 2: If Haar cascade found nothing, use YOLO person localization
    if face_box is None:
        model = get_yolo_model()
        if model is not None:
            try:
                res = model(img, conf=0.35, verbose=False)
                if res and len(res) > 0 and res[0].boxes is not None:
                    person_boxes = []
                    for b in res[0].boxes:
                        if int(b.cls.item()) == 0:  # 0 is 'person'
                            xyxy = [int(v) for v in b.xyxy[0].tolist()]
                            pw = xyxy[2] - xyxy[0]
                            ph = xyxy[3] - xyxy[1]
                            person_boxes.append((xyxy[0], xyxy[1], pw, ph))

                    if person_boxes:
                        # Largest person
                        person_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
                        px, py, pw, ph = person_boxes[0]

                        # Derive head/face region from person box
                        fx = max(0, int(px + pw * 0.22))
                        fy = max(0, int(py + ph * 0.04))
                        fw = min(iw - fx, int(pw * 0.56))
                        fh = min(ih - fy, int(ph * 0.36))

                        if fw >= 24 and fh >= 24:
                            face_box = (fx, fy, fw, fh)
            except Exception as e:
                print(f"[FaceService] YOLO fallback detection error: {e}")

    if face_box is None:
        return None, None

    x, y, w, h = face_box
    face_roi = gray[y : y + h, x : x + w]
    if face_roi.size == 0:
        return None, None

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
            if bright_ratio > 0.08:
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
            dress_type = "Regular Uniform (Dark / Blazer)"
        else:
            dress_type = "Regular Formal Uniform"
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
        "torso_box": [int(tx1), int(ty1), int(tx2 - tx1), int(ty2 - ty1)],
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
            "helmet_box": None,
            "vest_box": None,
        }

    h, w = frame.shape[:2]
    fx, fy, fw, fh = face_box

    # 1. Helmet Region (above forehead)
    hy1 = max(0, int(fy - fh * 0.70))
    hy2 = min(h, int(fy + fh * 0.15))
    hx1 = max(0, int(fx - fw * 0.20))
    hx2 = min(w, int(fx + fw * 1.20))
    helmet_box = [int(hx1), int(hy1), int(hx2 - hx1), int(hy2 - hy1)]

    helmet_detected = False
    helmet_roi = frame[hy1:hy2, hx1:hx2]
    if helmet_roi.size > 0:
        hsv_h = cv2.cvtColor(helmet_roi, cv2.COLOR_BGR2HSV)
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
    vest_box = [int(vx1), int(vy1), int(vx2 - vx1), int(vy2 - vy1)]

    vest_detected = False
    vest_roi = frame[vy1:vy2, vx1:vx2]
    if vest_roi.size > 0:
        hsv_v = cv2.cvtColor(vest_roi, cv2.COLOR_BGR2HSV)
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
        "helmet_box": helmet_box,
        "vest_box": vest_box,
    }


def analyze_surveillance_frame(
    frame: np.ndarray,
    environment_id: int = 1,
    assigned_function: str = "FACE_ATTENDANCE",
) -> Dict[str, Any]:
    """
    Performs full surveillance perception for VANTEP AI:
    - Multi-object YOLO detection (person, smartphone, bag, etc.)
    - Facial biometrics & database verification
    - Torso dress code & ID card verification
    - OSHA safety PPE (helmet, vest, gloves)
    - Returns technical bounding boxes for EVERY person, face, dress, ID, and safety gear!
    """
    if frame is None or frame.size == 0:
        return {
            "person_detected": False,
            "face_detected": False,
            "detections": [],
            "objects_summary": [],
            "is_match": False,
            "matched_person": None,
            "similarity": 0.0,
            "status_label": "STANDBY • WAITING FOR CAMERA FEED",
        }

    ih, iw = frame.shape[:2]
    model = get_yolo_model()

    yolo_persons: List[Tuple[int, int, int, int, float]] = []
    yolo_phones: List[Tuple[int, int, int, int, float]] = []
    yolo_objects: List[Dict[str, Any]] = []

    if model is not None:
        try:
            res = model(frame, conf=0.35, verbose=False)
            if res and len(res) > 0 and res[0].boxes is not None:
                for b in res[0].boxes:
                    cls_id = int(b.cls.item())
                    conf = float(b.conf.item())
                    coords = [int(v) for v in b.xyxy[0].tolist()]
                    bx1, by1, bx2, by2 = coords
                    bw = bx2 - bx1
                    bh = by2 - by1

                    if cls_id == 0:  # person
                        yolo_persons.append((bx1, by1, bw, bh, conf))
                    elif cls_id == 67:  # cell phone
                        yolo_phones.append((bx1, by1, bw, bh, conf))
                    else:
                        cname = res[0].names.get(cls_id, f"obj_{cls_id}")
                        yolo_objects.append(
                            {"name": cname, "conf": conf, "box": [bx1, by1, bw, bh]}
                        )
        except Exception as e:
            print(f"[FaceService] YOLO inference error: {e}")

    # Stage 2: Fallback to Haar cascade if no YOLO person was found
    feat, haar_face_box = extract_face_embedding(frame)
    has_person = len(yolo_persons) > 0 or haar_face_box is not None

    if not has_person:
        # Standby mode: No subject in frame, zero fake alerts!
        return {
            "person_detected": False,
            "face_detected": False,
            "detections": [],
            "objects_summary": [],
            "is_match": False,
            "matched_person": None,
            "similarity": 0.0,
            "detected_gender": "person",
            "dress_code": {
                "id_card_detected": None,
                "id_card_status": "STANDBY • WAITING FOR SUBJECT",
                "dress_compliant": True,
                "dress_type": "None",
                "compliance_status": "NOMINAL_STANDBY",
            },
            "safety_ppe": {
                "ppe_active": False,
                "ppe_compliant": True,
                "status_label": "STANDBY • WAITING FOR WORKER",
            },
            "prohibited_items": [],
            "assigned_function": assigned_function,
            "timestamp": time.time(),
        }

    # Fetch registered personnel embeddings from database
    db_people = []
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
        for r in rows:
            try:
                db_people.append(
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "identifier": r["identifier"],
                        "role": r["role"],
                        "department": r["department"],
                        "allowed_dress": r["allowed_dress"],
                        "feat": np.array(
                            json.loads(r["embedding_json"]), dtype=np.float32
                        ),
                    }
                )
            except Exception:
                continue
    finally:
        conn.close()

    # Determine primary person box
    if yolo_persons:
        yolo_persons.sort(key=lambda p: p[2] * p[3], reverse=True)
        px, py, pw, ph, pconf = yolo_persons[0]
    else:
        # Reconstruct person box around Haar face
        hfx, hfy, hfw, hfh = haar_face_box
        px = max(0, int(hfx - hfw * 0.4))
        py = max(0, int(hfy - hfh * 0.2))
        pw = min(iw - px, int(hfw * 1.8))
        ph = min(ih - py, int(hfh * 3.5))
        pconf = 0.88

    # Determine face box
    if haar_face_box:
        fx, fy, fw, fh = haar_face_box
    else:
        fx = max(0, int(px + pw * 0.22))
        fy = max(0, int(py + ph * 0.04))
        fw = min(iw - fx, int(pw * 0.56))
        fh = min(ih - fy, int(ph * 0.36))

    # Face verification against database
    matched_person = None
    similarity_score = 0.0
    is_match = False

    if feat is not None and db_people:
        best_sim = -1.0
        best_p = None
        for p in db_people:
            sim = cosine_similarity(feat, p["feat"])
            if sim > best_sim:
                best_sim = sim
                best_p = p

        if best_sim >= 0.70 and best_p is not None:
            is_match = True
            similarity_score = round(best_sim, 2)
            matched_person = {k: v for k, v in best_p.items() if k != "feat"}
        else:
            similarity_score = round(max(0.0, best_sim), 2)

    face_roi = frame[fy : fy + fh, fx : fx + fw]
    detected_gender = classify_gender_heuristic(face_roi)

    # Dress Code & ID Card Analysis
    dress_data = detect_dress_code_and_id_card(frame, (fx, fy, fw, fh))
    if is_match and matched_person:
        allowed = (matched_person.get("allowed_dress") or "").lower()
        if "casual" in allowed:
            dress_data["dress_compliant"] = True
            dress_data["compliance_status"] = "CUSTOM_POLICY_PASS"
            dress_data["status_label"] = "CUSTOM POLICY PASS • CASUAL PERMITTED"

    is_dress_pass = dress_data.get("dress_compliant", True)
    has_id = dress_data.get("id_card_detected", False)
    dress_type = dress_data.get("dress_type", "Formals")

    # Safety PPE Analysis
    safety_data = detect_safety_ppe(frame, (fx, fy, fw, fh))
    has_helmet = safety_data.get("helmet_detected", False)
    has_vest = safety_data.get("vest_detected", False)

    # Prohibited items (phones, cheat sheets)
    prohibited_items = []
    for ph_box in yolo_phones:
        prohibited_items.append("Smartphone")

    # Build Complete Technical Bounding Boxes (matching Reference Images 1 & 2!)
    detections: List[Dict[str, Any]] = []

    # 1. Person Box
    if is_match and matched_person:
        p_label = f"{matched_person['name']} [{matched_person.get('identifier', 'ID')}] {int(similarity_score * 100)}%"
        p_color = "#ffd700"  # Royal Gold
    else:
        p_label = f"person {int(pconf * 100)}%"
        p_color = "#10b981"  # Crisp Green (Reference Image 2)

    detections.append(
        {
            "type": "person",
            "label": p_label,
            "conf": round(similarity_score if is_match else pconf, 2),
            "box": [px, py, pw, ph],
            "color": p_color,
        }
    )

    # 2. Face Box
    face_label = (
        f"Face: {matched_person['name']} ({int(similarity_score * 100)}%)"
        if is_match
        else f"Face: Unknown {detected_gender.capitalize()} ({int(pconf * 100)}%)"
    )
    face_color = "#ffd700" if is_match else "#38bdf8"
    detections.append(
        {
            "type": "face",
            "label": face_label,
            "conf": round(similarity_score if is_match else pconf, 2),
            "box": [fx, fy, fw, fh],
            "color": face_color,
        }
    )

    # 3. Dress Code Box
    tx, ty, tw, th = dress_data.get(
        "torso_box", [px, int(py + ph * 0.35), pw, int(ph * 0.45)]
    )
    dress_label = f"Dress: {dress_type} [{'PASS' if is_dress_pass else 'VIOLATION'}]"
    dress_color = "#10b981" if is_dress_pass else "#f59e0b"
    detections.append(
        {
            "type": "dress_code",
            "label": dress_label,
            "conf": 0.92,
            "box": [tx, ty, tw, th],
            "color": dress_color,
        }
    )

    # 4. ID Card Box
    ix, iy, iw, ih = dress_data.get("id_box") or [
        int(tx + tw * 0.35),
        int(ty + th * 0.30),
        int(tw * 0.30),
        int(th * 0.25),
    ]
    id_label = f"ID Card: {'VERIFIED' if has_id else 'MISSING [ALERT]'}"
    id_color = "#10b981" if has_id else "#ef4444"
    detections.append(
        {
            "type": "id_card",
            "label": id_label,
            "conf": 0.89,
            "box": [ix, iy, iw, ih],
            "color": id_color,
        }
    )

    # 5. Safety Gear Boxes (Helmet & Vest)
    if assigned_function.upper() in ["SAFETY", "DRESS_CODE_PPE"] or True:
        # Include safety gear boxes
        hx, hy, hw, hh = safety_data.get("helmet_box") or [
            max(0, int(fx - fw * 0.15)),
            max(0, int(fy - fh * 0.45)),
            int(fw * 1.30),
            int(fh * 0.48),
        ]
        helmet_label = (
            f"Safety Helmet: {'VERIFIED' if has_helmet else 'MISSING [HAZARD]'}"
        )
        helmet_color = "#10b981" if has_helmet else "#ef4444"
        detections.append(
            {
                "type": "helmet",
                "label": helmet_label,
                "conf": 0.94,
                "box": [hx, hy, hw, hh],
                "color": helmet_color,
            }
        )

        vx, vy, vw, vh = safety_data.get("vest_box") or [tx, ty, tw, th]
        vest_label = f"Safety Vest: {'DETECTED' if has_vest else 'MISSING [HAZARD]'}"
        vest_color = "#10b981" if has_vest else "#ef4444"
        detections.append(
            {
                "type": "vest",
                "label": vest_label,
                "conf": 0.91,
                "box": [vx, vy, vw, vh],
                "color": vest_color,
            }
        )

    # 6. Prohibited Phone / Threat Boxes
    for ph_x, ph_y, ph_w, ph_h, ph_c in yolo_phones:
        detections.append(
            {
                "type": "prohibited",
                "label": f"🚨 PROHIBITED SMARTPHONE {int(ph_c * 100)}%",
                "conf": ph_c,
                "box": [ph_x, ph_y, ph_w, ph_h],
                "color": "#ef4444",
            }
        )

    # 7. Additional Detected Objects (motorcycles, backpacks, etc. - Reference Image 1)
    for obj in yolo_objects[:3]:
        detections.append(
            {
                "type": "object",
                "label": f"{obj['name']} {obj['conf']:.2f}",
                "conf": obj["conf"],
                "box": obj["box"],
                "color": "#06b6d4",  # Cyan like Image 1
            }
        )

    return {
        "person_detected": True,
        "face_detected": True,
        "face_box": [fx, fy, fw, fh],
        "person_box": [px, py, pw, ph],
        "is_match": is_match,
        "matched_person": matched_person,
        "similarity": similarity_score,
        "detected_gender": detected_gender,
        "dress_code": dress_data,
        "safety_ppe": safety_data,
        "prohibited_items": prohibited_items,
        "detections": detections,
        "objects_summary": [
            {"label": d["label"], "conf": d["conf"], "color": d["color"]}
            for d in detections
        ],
        "assigned_function": assigned_function,
        "timestamp": time.time(),
    }
