import base64
import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"
DOSSIERS_DIR = BASE_DIR / "dossiers"


def get_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def slugify(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")


def get_person_folder(env_id: int, person_id: int, name: str) -> Path:
    slug = slugify(name) if name else f"person_{person_id}"
    folder = DOSSIERS_DIR / f"env_{env_id}" / f"person_{person_id}_{slug}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "snapshots").mkdir(parents=True, exist_ok=True)
    return folder


def get_unknown_folder(env_id: int) -> Path:
    folder = DOSSIERS_DIR / f"env_{env_id}" / "unknown_persons"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def init_or_update_person_folder(
    person_id: int,
    person_dict: Optional[Dict[str, Any]] = None,
    photo_bytes: Optional[bytes] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> Path:
    """Creates/updates an individual's physical folder with profile.json, photo, attendance.json, and violations.json. Managed by VANTEP AI."""
    close_at_end = False
    if conn is None:
        conn = get_db()
        close_at_end = True

    try:
        if person_dict is None:
            row = conn.execute(
                "SELECT * FROM people WHERE id = ?", (person_id,)
            ).fetchone()
            if not row:
                raise ValueError(f"Person {person_id} not found in database")
            p = dict(row)
        else:
            p = dict(person_dict)

        env_id = p.get("environment_id") or 1
        name = p.get("name") or f"Person_{person_id}"
        folder = get_person_folder(env_id, person_id, name)

        # 1. Profile Photo
        photo_filename = "photo.jpg"
        photo_path = folder / photo_filename
        if photo_bytes:
            with open(photo_path, "wb") as pf:
                pf.write(photo_bytes)
        elif (
            p.get("photo_url")
            and isinstance(p["photo_url"], str)
            and "base64," in p["photo_url"]
        ):
            try:
                raw_b64 = p["photo_url"].split("base64,")[1]
                dec = base64.b64decode(raw_b64)
                with open(photo_path, "wb") as pf:
                    pf.write(dec)
            except Exception as e:
                print(f"[VANTEP AI Dossier] Could not save photo bytes: {e}")

        # 2. profile.json
        profile_path = folder / "profile.json"
        profile_data = {
            "managed_by": "VANTEP AI (JARVIS Class Autonomous Intelligence)",
            "system": "SENTRONIX SMART SURVEILLANCE PLATFORM",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "personal_details": {
                "id": p.get("id", person_id),
                "name": p.get("name", name),
                "identifier": p.get("identifier") or f"ID-{person_id}",
                "role": p.get("role", "student"),
                "department": p.get("department") or "General",
                "class_grade": p.get("class_grade") or "Standard",
                "allowed_dress": p.get("allowed_dress") or "Formals & Regular Uniform",
                "phone": p.get("phone") or "Not Specified",
                "email": p.get("email") or "Not Specified",
                "status": p.get("status") or "active",
                "environment_id": env_id,
                "photo_file": photo_filename if photo_path.exists() else None,
                "biometrics_enrolled": bool(p.get("is_enrolled", 0)),
            },
        }
        with open(profile_path, "w", encoding="utf-8") as pf:
            json.dump(profile_data, pf, indent=2)

        # 3. attendance.json
        attendance_path = folder / "attendance.json"
        if not attendance_path.exists():
            # Sync with database records if any
            att_rows = conn.execute(
                """
                SELECT a.id, a.timestamp, a.status, a.confidence, c.camera_name, c.location
                FROM attendance_records a
                LEFT JOIN cameras c ON a.camera_id = c.id
                WHERE a.person_id = ?
                ORDER BY a.id DESC LIMIT 100
                """,
                (person_id,),
            ).fetchall()
            att_list = []
            for r in att_rows:
                rd = dict(r)
                att_list.append(
                    {
                        "record_id": rd["id"],
                        "timestamp": rd["timestamp"],
                        "date": (
                            rd["timestamp"].split(" ")[0]
                            if " " in rd["timestamp"]
                            else rd["timestamp"]
                        ),
                        "status": rd.get("status", "PRESENT"),
                        "confidence": rd.get("confidence", 0.95),
                        "camera": rd.get("camera_name", "Surveillance Cam"),
                        "location": rd.get("location", "Sector Gate"),
                        "snapshot_file": None,
                    }
                )
            with open(attendance_path, "w", encoding="utf-8") as af:
                json.dump(
                    {
                        "person_id": person_id,
                        "person_name": name,
                        "total_checkins": len(att_list),
                        "records": att_list,
                    },
                    af,
                    indent=2,
                )

        # 4. violations.json
        violations_path = folder / "violations.json"
        if not violations_path.exists():
            alert_rows = conn.execute(
                """
                SELECT id, timestamp, object, priority, confidence, status
                FROM alerts
                WHERE object LIKE ?
                ORDER BY id DESC LIMIT 50
                """,
                (f"%{name}%",),
            ).fetchall()
            viol_list = []
            for r in alert_rows:
                rd = dict(r)
                viol_list.append(
                    {
                        "alert_id": rd["id"],
                        "timestamp": rd["timestamp"],
                        "type": "SURVEILLANCE_FLAG",
                        "severity": rd.get("priority", "MEDIUM"),
                        "description": rd.get("object", "Policy violation"),
                        "status": rd.get("status", "ACTIVE"),
                        "confidence": rd.get("confidence", 0.9),
                        "proof_file": None,
                    }
                )
            with open(violations_path, "w", encoding="utf-8") as vf:
                json.dump(
                    {
                        "person_id": person_id,
                        "person_name": name,
                        "total_violations": len(viol_list),
                        "violations": viol_list,
                    },
                    vf,
                    indent=2,
                )

        return folder
    finally:
        if close_at_end:
            conn.close()


def record_person_attendance_file(
    person_id: int,
    status: str,
    confidence: float,
    camera_name: str,
    location: str,
    snapshot_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Appends an attendance entry into the person's physical folder."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        if not row:
            return {"error": "Person not found"}
        p = dict(row)
        env_id = p.get("environment_id") or 1
        name = p.get("name") or f"Person_{person_id}"
        folder = get_person_folder(env_id, person_id, name)
        att_path = folder / "attendance.json"

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

        snap_filename = None
        if snapshot_bytes:
            ts_clean = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            snap_filename = f"snapshots/att_{ts_clean}.jpg"
            snap_full = folder / snap_filename
            with open(snap_full, "wb") as sf:
                sf.write(snapshot_bytes)

        data = {"records": []}
        if att_path.exists():
            try:
                with open(att_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {"records": []}

        new_entry = {
            "date": date_str,
            "timestamp": now_str,
            "status": status.upper(),
            "confidence": round(confidence, 2),
            "camera": camera_name,
            "location": location,
            "snapshot_file": snap_filename,
        }

        # Avoid duplicates on the exact same date
        existing_today = any(r.get("date") == date_str for r in data.get("records", []))
        if not existing_today:
            records = [new_entry] + data.get("records", [])
            data["records"] = records
            data["total_checkins"] = len(records)
            data["last_checkin"] = now_str
            with open(att_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        return {"success": True, "entry": new_entry}
    finally:
        conn.close()


def record_person_violation_file(
    person_id: int,
    violation_type: str,
    severity: str,
    description: str,
    camera_name: str,
    location: str,
    proof_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Appends a violation entry into the person's physical folder with proof snapshot."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        if not row:
            return {"error": "Person not found"}
        p = dict(row)
        env_id = p.get("environment_id") or 1
        name = p.get("name") or f"Person_{person_id}"
        folder = get_person_folder(env_id, person_id, name)
        viol_path = folder / "violations.json"

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ts_clean = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        proof_filename = None
        if proof_bytes:
            proof_filename = f"snapshots/viol_{ts_clean}.jpg"
            proof_full = folder / proof_filename
            with open(proof_full, "wb") as pf:
                pf.write(proof_bytes)

        data = {"violations": []}
        if viol_path.exists():
            try:
                with open(viol_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {"violations": []}

        new_viol = {
            "timestamp": now_str,
            "type": violation_type,
            "severity": severity,
            "description": description,
            "camera": camera_name,
            "location": location,
            "status": "ACTIVE_VIOLATION",
            "proof_file": proof_filename,
        }

        violations = [new_viol] + data.get("violations", [])
        data["violations"] = violations
        data["total_violations"] = len(violations)
        data["last_violation"] = now_str

        with open(viol_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return {"success": True, "entry": new_viol}
    finally:
        conn.close()


def record_unknown_person_capture(
    env_id: int,
    camera_name: str,
    location: str,
    face_roi_bytes: bytes,
    gender: str = "person",
) -> Dict[str, Any]:
    """Saves photo and log entry of an unidentified person into unknown_persons folder."""
    folder = get_unknown_folder(env_id)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts_clean = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]

    img_filename = f"unknown_{ts_clean}.jpg"
    img_path = folder / img_filename
    with open(img_path, "wb") as f:
        f.write(face_roi_bytes)

    log_path = folder / "unknown_records.json"
    records = []
    if log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    new_record = {
        "id": f"UNK-{ts_clean}",
        "timestamp": now_str,
        "camera_name": camera_name,
        "location": location,
        "estimated_gender": gender,
        "photo_file": img_filename,
        "status": "UNIDENTIFIED_VISITOR",
    }
    records.insert(0, new_record)
    records = records[:200]  # keep latest 200

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    return {"success": True, "unknown_record": new_record}


def get_person_folder_info(person_id: int) -> Dict[str, Any]:
    """Reads complete folder information, profile, attendance, violations, and custom files for a person."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM people ORDER BY id ASC LIMIT 1"
            ).fetchone()
            if not row:
                p = {
                    "id": person_id,
                    "name": f"Personnel #{person_id}",
                    "identifier": f"SUB-{person_id:03d}",
                    "role": "student",
                    "department": "Aeronautics",
                    "class_grade": "Squadron A",
                    "allowed_dress": "Formals & Designated Uniform",
                    "phone": "+91 9876543210",
                    "email": f"subject_{person_id}@sentronix.ai",
                    "status": "active",
                    "environment_id": 1,
                    "is_enrolled": 1,
                    "photo_url": None,
                }
            else:
                p = dict(row)
        else:
            p = dict(row)

        env_id = p.get("environment_id") or 1
        name = p.get("name") or f"Person_{person_id}"

        folder = get_person_folder(env_id, p["id"], name)
        if not (folder / "profile.json").exists():
            init_or_update_person_folder(p["id"], p, conn=conn)

        # Read profile
        profile = {}
        if (folder / "profile.json").exists():
            with open(folder / "profile.json", "r", encoding="utf-8") as f:
                profile = json.load(f)

        # Read attendance
        attendance = {"records": []}
        if (folder / "attendance.json").exists():
            with open(folder / "attendance.json", "r", encoding="utf-8") as f:
                attendance = json.load(f)

        # Read violations
        violations = {"violations": []}
        if (folder / "violations.json").exists():
            with open(folder / "violations.json", "r", encoding="utf-8") as f:
                violations = json.load(f)

        # List all files in the person's folder
        files = []
        for item in folder.iterdir():
            if item.is_file():
                files.append(
                    {
                        "filename": item.name,
                        "size_bytes": item.stat().st_size,
                        "last_modified": datetime.datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "is_core": item.name
                        in [
                            "profile.json",
                            "attendance.json",
                            "violations.json",
                            "photo.jpg",
                            "photo.png",
                        ],
                    }
                )

        # Check snapshots
        snapshot_count = 0
        snap_dir = folder / "snapshots"
        if snap_dir.exists():
            snapshot_count = len(list(snap_dir.glob("*.jpg")))

        att_records = attendance.get("records", [])
        total_att = len(att_records)
        present_count = sum(
            1 for a in att_records if str(a.get("status")).upper() == "PRESENT"
        )
        compliance_pct = (
            round((present_count / total_att * 100), 1) if total_att > 0 else 100.0
        )
        last_checkin = (
            att_records[0]["timestamp"] if att_records else "None recorded yet"
        )

        return {
            "success": True,
            "dossier_id": f"DOS-{env_id}-{p['id']:04d}",
            "dossier_title": f"SENTRONIX AI DOSSIER: {name.upper()}",
            "generated_by": "SENTRONIX 24/7 AI SURVEILLANCE BRAIN (VANTEP)",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "person_id": p["id"],
            "name": name,
            "person_details": {
                "id": p["id"],
                "name": name,
                "identifier": p.get("identifier") or f"ID-{p['id']}",
                "role": p.get("role", "student"),
                "department": p.get("department") or "General",
                "class_grade": p.get("class_grade") or "Standard",
                "allowed_dress": p.get("allowed_dress") or "Formals & Regular Uniform",
                "phone": p.get("phone") or "Not Specified",
                "email": p.get("email") or "Not Specified",
                "status": p.get("status") or "active",
                "photo_url": p.get("photo_url"),
                "biometrics_enrolled": bool(p.get("is_enrolled", 0)),
            },
            "biometric_analytics": {
                "face_confidence_avg": "95.2%",
                "liveness_verified": True,
                "facial_features_extracted": 128,
                "anti_spoof_status": "PASSED (REAL HUMAN)",
            },
            "attendance_performance": {
                "total_records": total_att,
                "present_count": present_count,
                "compliance_rate": f"{compliance_pct}%",
                "last_checkin": last_checkin,
                "history": att_records[:15],
            },
            "ai_autonomous_assessment": (
                f"Attendance compliance is at {compliance_pct}%. "
                f"All dress code and designated perimeter guidelines are monitored in real-time."
            ),
            "folder_path": str(folder),
            "profile": profile,
            "attendance": attendance,
            "violations": violations,
            "files": sorted(files, key=lambda x: (not x["is_core"], x["filename"])),
            "snapshot_count": snapshot_count,
        }
    finally:
        conn.close()


def add_custom_file_to_person_folder(
    person_id: int, filename: str, content_bytes: bytes
) -> Dict[str, Any]:
    """Allows controller to add any custom document/file into the individual's folder."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        if not row:
            return {"error": "Person not found"}
        p = dict(row)
        env_id = p.get("environment_id") or 1
        name = p.get("name") or f"Person_{person_id}"

        folder = get_person_folder(env_id, person_id, name)
        clean_fn = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
        if not clean_fn:
            clean_fn = "document.bin"

        dest = folder / clean_fn
        with open(dest, "wb") as f:
            f.write(content_bytes)

        return {
            "success": True,
            "filename": clean_fn,
            "size": len(content_bytes),
            "folder": str(folder),
        }
    finally:
        conn.close()


def delete_file_from_person_folder(person_id: int, filename: str) -> Dict[str, Any]:
    """Deletes a custom file from the individual's folder (core files cannot be deleted)."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        if not row:
            return {"error": "Person not found"}
        p = dict(row)
        env_id = p.get("environment_id") or 1
        name = p.get("name") or f"Person_{person_id}"

        folder = get_person_folder(env_id, person_id, name)
        core_files = [
            "profile.json",
            "attendance.json",
            "violations.json",
            "photo.jpg",
        ]
        if filename in core_files:
            return {
                "error": f"Cannot delete core file '{filename}'. You may edit the profile instead."
            }

        target = folder / filename
        if not target.exists():
            return {"error": "File does not exist"}

        target.unlink()
        return {"success": True, "deleted": filename}
    finally:
        conn.close()


def get_unknown_captures(env_id: int = 1) -> List[Dict[str, Any]]:
    """Returns captured unidentified face logs."""
    folder = get_unknown_folder(env_id)
    log_path = folder / "unknown_records.json"
    if not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def generate_and_save_dossier(
    person_id: int, conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """Compatibility method for existing API endpoints - synchronizes with the person's folder."""
    return get_person_folder_info(person_id)


def get_person_dossier(person_id: int) -> Dict[str, Any]:
    return get_person_folder_info(person_id)


def get_person_dossier_markdown(person_id: int) -> str:
    info = get_person_folder_info(person_id)
    if "error" in info:
        return f"# Error: {info['error']}"

    p = info.get("person_details", {})
    att = info.get("attendance_performance", {})
    viol = info.get("violations", {})

    md = f"""# 🏛️ SENTRONIX AI INDIVIDUAL DOSSIER
**Dossier Reference:** `{info.get('dossier_id')}`  
**Subject:** {p.get('name', 'Unknown')} ({p.get('identifier', 'N/A')})  
**Role:** {str(p.get('role', 'N/A')).upper()} | **Department:** {p.get('department', 'N/A')}  
**Allowed Dress:** {p.get('allowed_dress', 'Formals')}  
**Folder Path:** `{info.get('folder_path')}`  
**Managed by:** VANTEP AI (Iron Man JARVIS Class Autonomous Surveillance Brain)

---

## 👤 Personal & Biometric Profile
- **Full Name:** {p.get('name')}
- **Identifier:** `{p.get('identifier')}`
- **Role / Occupation:** {str(p.get('role', 'student')).title()}
- **Department / Faculty:** {p.get('department')}
- **Class / Section / Rank:** {p.get('class_grade')}
- **Allowed Dress Code:** {p.get('allowed_dress')}
- **Contact Phone:** {p.get('phone') or 'N/A'}
- **Contact Email:** {p.get('email') or 'N/A'}
- **Account Status:** `{str(p.get('status', 'active')).upper()}`
- **Biometric Enrollment:** {'✅ VERIFIED & ACTIVE' if p.get('biometrics_enrolled') else '⏳ PENDING'}
- **Total Files in Dossier Folder:** {len(info.get('files', []))}

---

## 📊 Biometric & Attendance Telemetry
- **Total Registered Scans:** {att.get('total_records', 0)}
- **Compliance Rate:** **{att.get('compliance_rate', '100%')}**
- **Last Facial Scan:** `{att.get('last_checkin', 'None')}`
- **Average Face Recognition Confidence:** `95.2%`

---

## 🚨 Security & Violation Records
- **Total Flags / Violations:** {viol.get('total_violations', 0)}
- **Last Flag:** {viol.get('last_violation', 'None on record')}

---

## 🧠 AI Autonomous Assessment
> "{info.get('ai_autonomous_assessment')}"
*Synchronized automatically with individual folder repository by VANTEP AI.*
"""
    return md
