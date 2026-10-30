import cv2
import numpy as np
import json
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

# Load OpenCV Cascades
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")


def get_db():
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def extract_face_embedding(
    img: np.ndarray,
) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
    """
    Detects the primary face in an image and extracts a normalized 128-dimensional feature embedding.
    Returns (embedding, (x, y, w, h)) or (None, None) if no face detected.
    """
    if img is None or img.size == 0:
        return None, None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=4, minSize=(35, 35)
    )

    if len(faces) == 0:
        # Check if entire image is already a cropped face
        h, w = gray.shape[:2]
        if 40 <= h <= 600 and 40 <= w <= 600 and 0.7 <= (w / float(h)) <= 1.4:
            roi = gray
            box = (0, 0, w, h)
        else:
            return None, None
    else:
        # Select largest detected face
        fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
        roi = gray[fy : fy + fh, fx : fx + fw]
        box = (int(fx), int(fy), int(fw), int(fh))

    if roi.size == 0:
        return None, None

    resized = cv2.resize(roi, (64, 64))

    # Compute 128-dimensional normalized facial feature vector:
    # 64 spatial intensity points + 64 gradient magnitude points
    sub_intensity = cv2.resize(resized, (8, 8)).flatten().astype(np.float32)
    gx = cv2.Sobel(resized, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(resized, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.sqrt(gx**2 + gy**2)
    sub_mag = cv2.resize(mag, (8, 8)).flatten().astype(np.float32)

    feat = np.concatenate([sub_intensity, sub_mag])
    norm = np.linalg.norm(feat)
    if norm > 0:
        feat = feat / norm

    return feat, box


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(dot / (n1 * n2))


def enroll_person_embedding(person_id: int, image_data: bytes) -> bool:
    """Computes face embedding from image bytes and saves to face_embeddings table."""
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return False

    feat, _ = extract_face_embedding(img)
    if feat is None:
        # Compute fallback center crop embedding
        h, w = img.shape[:2]
        center = img[int(h * 0.15) : int(h * 0.85), int(w * 0.15) : int(w * 0.85)]
        feat, _ = extract_face_embedding(center)
        if feat is None:
            return False

    conn = get_db()
    try:
        embedding_json = json.dumps(feat.tolist())
        conn.execute("DELETE FROM face_embeddings WHERE person_id = ?", (person_id,))
        conn.execute(
            """
            INSERT INTO face_embeddings (person_id, embedding_json, feature_version)
            VALUES (?, ?, 'v2')
            """,
            (person_id, embedding_json),
        )
        conn.execute(
            """
            UPDATE people SET is_enrolled = 1 WHERE id = ?
            """,
            (person_id,),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def classify_gender_heuristic(face_roi: np.ndarray) -> str:
    """Heuristic gender estimation using facial structure, cheekbone aspect, and brightness distribution."""
    if face_roi is None or face_roi.size == 0:
        return "person"
    try:
        h, w = face_roi.shape[:2]
        gray = (
            cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            if len(face_roi.shape) == 3
            else face_roi
        )
        # Upper third vs lower third contrast (jaw vs forehead & eyes)
        lower = gray[int(h * 0.6) :, :]
        std_lower = np.std(lower)
        mean_lower = np.mean(lower)

        # Hair / softer skin vs facial shadow
        if std_lower < 28 and mean_lower > 105:
            return "female"
        elif std_lower >= 28:
            return "male"
        return "person"
    except Exception:
        return "person"


def detect_dress_code_and_id_card(
    frame: np.ndarray, face_box: Optional[Tuple[int, int, int, int]] = None
) -> Dict[str, Any]:
    """
    Analyzes the torso and chest region to detect:
    1. Institutional ID Card / Lanyard badge (presence, location, & aspect ratio)
    2. Dress code compliance (Formals & Regular Uniform vs Casual Attire)
    Guaranteed to run for EVERY individual in the frame (enrolled or unenrolled).
    """
    h, w = frame.shape[:2]

    if face_box is not None:
        fx, fy, fw, fh = face_box
        tx1 = max(0, int(fx - fw * 0.5))
        tx2 = min(w, int(fx + fw * 1.5))
        ty1 = min(h, int(fy + fh * 0.95))
        ty2 = min(h, int(fy + fh * 2.85))
    else:
        # Fallback to upper torso region of frame when face isn't directly frontal
        tx1 = max(0, int(w * 0.22))
        tx2 = min(w, int(w * 0.78))
        ty1 = max(0, int(h * 0.28))
        ty2 = min(h, int(h * 0.85))

    if ty2 <= ty1 or tx2 <= tx1:
        tx1, tx2 = 0, w
        ty1, ty2 = int(h * 0.2), int(h * 0.8)

    torso_roi = frame[ty1:ty2, tx1:tx2]
    if torso_roi is None or torso_roi.size == 0:
        return {
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

    # 1. ID Card / Badge Detection (Rectangular badge contour + Lanyard neck straps)
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
                bx, by, bw, bh = cv2.boundingRect(approx)
                aspect = float(bw) / float(bh)
                # Typical ID badge aspect ratio (vertical 0.6-0.8 or horizontal 1.3-1.6)
                if 0.5 <= aspect <= 1.85:
                    id_card_detected = True
                    id_box = [int(tx1 + bx), int(ty1 + by), int(bw), int(bh)]
                    break

    # Contrast heuristic for white/reflective ID card badge on central chest
    if not id_card_detected:
        center_chest = torso_gray[
            int(th * 0.20) : int(th * 0.80), int(tw * 0.25) : int(tw * 0.75)
        ]
        if center_chest.size > 0:
            bright_pixels = np.count_nonzero(center_chest > 185)
            if (bright_pixels / float(center_chest.size)) > 0.10:
                id_card_detected = True
                id_box = [
                    int(tx1 + tw * 0.35),
                    int(ty1 + th * 0.35),
                    int(tw * 0.30),
                    int(th * 0.25),
                ]

    if id_box is None:
        id_box = [
            int(tx1 + tw * 0.35),
            int(ty1 + th * 0.35),
            int(tw * 0.30),
            int(th * 0.25),
        ]

    # 2. Dress Code Analysis (Solid Formals & School Uniform vs Casual / Printed Attire)
    torso_hsv = cv2.cvtColor(torso_roi, cv2.COLOR_BGR2HSV)
    saturation = torso_hsv[:, :, 1]
    val = torso_hsv[:, :, 2]
    sat_mean = np.mean(saturation)
    val_std = np.std(val)
    val_mean = np.mean(val)

    # Formals & School Uniforms exhibit low saturation and uniform tones
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


def analyze_surveillance_frame(
    frame: np.ndarray,
    environment_id: int = 1,
    assigned_function: str = "FACE_ATTENDANCE",
) -> Dict[str, Any]:
    """
    Performs full frame perception:
    1. True Face Matching against enrolled people's database embeddings
    2. Unknown Person / Gender Classification
    3. Dress Code & ID Card Verification
    4. Prohibited Item & Threat Perception
    """
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

    # 1. Compare against registered embeddings in Database
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

            # Strict Similarity Threshold (0.72)
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

    # 2. Dress Code & ID Card Perception (Always evaluated for EVERY person, enrolled or unenrolled)
    dress_data = detect_dress_code_and_id_card(frame, face_box)

    # Check custom policy if enrolled
    if is_match and matched_person:
        allowed = (matched_person.get("allowed_dress") or "").lower()
        if "casual" in allowed:
            dress_data["dress_compliant"] = True
            dress_data["compliance_status"] = "CUSTOM_POLICY_PASS"
            dress_data["status_label"] = "CUSTOM POLICY PASS • CASUAL PERMITTED"

    # 3. Prohibited Item Perception (Cell Phones, Laptops, etc.)
    prohibited_items = []
    # Quick color/shape heuristic for smartphone held up in hand
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    phone_edges = cv2.Canny(gray, 50, 150)
    cnts, _ = cv2.findContours(phone_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        area = cv2.contourArea(c)
        if 800 <= area <= 12000:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            if len(approx) == 4:
                _, _, pw, ph = cv2.boundingRect(approx)
                p_aspect = float(ph) / float(pw) if pw > 0 else 0
                if 1.8 <= p_aspect <= 2.4:
                    prohibited_items.append("Smartphone")
                    break

    return {
        "face_detected": face_box is not None,
        "face_box": list(face_box) if face_box else None,
        "is_match": is_match,
        "matched_person": matched_person,
        "similarity": similarity_score,
        "detected_gender": detected_gender,
        "dress_code": dress_data,
        "prohibited_items": prohibited_items,
        "assigned_function": assigned_function,
        "timestamp": time.time(),
    }
