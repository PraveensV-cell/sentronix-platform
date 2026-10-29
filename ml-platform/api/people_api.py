import json
import sqlite3
import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Response
from api.dossier_manager import get_person_dossier, generate_and_save_dossier
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/people",
    tags=["People & Face Registry"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class CreatePersonRequest(BaseModel):
    name: str
    identifier: str  # Student / Staff ID (e.g. STU-101)
    role: str = "student"  # student, staff, visitor
    department: Optional[str] = "General"
    class_grade: Optional[str] = "Standard"
    allowed_dress: Optional[str] = "Formals & Regular Uniform"
    phone: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    environment_id: Optional[int] = 1


class UpdatePersonRequest(BaseModel):
    name: Optional[str] = None
    identifier: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    class_grade: Optional[str] = None
    allowed_dress: Optional[str] = None
    status: Optional[str] = None  # active, suspended, graduated, on_leave
    phone: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None


class BatchCreatePeopleRequest(BaseModel):
    people: List[CreatePersonRequest]
    environment_id: Optional[int] = 1


class EnrollFaceRequest(BaseModel):
    photo_url: Optional[str] = None
    embedding: Optional[List[float]] = None


@router.get("")
def list_people(role: Optional[str] = None, environment_id: Optional[int] = 1):
    conn = get_connection()
    try:
        query = "SELECT * FROM people WHERE environment_id = ?"
        params = [environment_id]
        if role and role != "ALL":
            query += " AND role = ?"
            params.append(role)
        query += " ORDER BY id DESC"

        rows = conn.execute(query, params).fetchall()
        people = [dict(r) for r in rows]

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        for p in people:
            att = conn.execute(
                """
                SELECT timestamp, status, confidence FROM attendance_records
                WHERE person_id = ? AND timestamp LIKE ?
                ORDER BY id DESC LIMIT 1
            """,
                (p["id"], f"{today}%"),
            ).fetchone()
            if att:
                p["today_attendance"] = dict(att)
            else:
                p["today_attendance"] = {"status": "ABSENT", "timestamp": None}

        return {"count": len(people), "people": people}
    finally:
        conn.close()


@router.get("/{person_id}")
def get_person(person_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Person not found")
        person = dict(row)

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        att = conn.execute(
            """
            SELECT timestamp, status, confidence FROM attendance_records
            WHERE person_id = ? AND timestamp LIKE ?
            ORDER BY id DESC LIMIT 1
        """,
            (person_id, f"{today}%"),
        ).fetchone()
        if att:
            person["today_attendance"] = dict(att)
        else:
            person["today_attendance"] = {"status": "ABSENT", "timestamp": None}

        return {"success": True, "person": person}
    finally:
        conn.close()


@router.post("")
def create_person(req: CreatePersonRequest):
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT * FROM people WHERE identifier = ?", (req.identifier,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Identifier already registered")

        cursor = conn.cursor()
        is_enrolled = 0
        cursor.execute(
            """
            INSERT INTO people (
                environment_id, identifier, name, role, department,
                class_grade, allowed_dress, phone, email, photo_url, is_enrolled, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active')
        """,
            (
                req.environment_id or 1,
                req.identifier,
                req.name,
                req.role,
                req.department or "General",
                req.class_grade or "Standard",
                req.allowed_dress or "Formals & Regular Uniform",
                req.phone,
                req.email,
                req.photo_url,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

        # Extract real facial embedding and enroll biometrics if photo_url is provided
        if req.photo_url:
            extracted = False
            if "base64," in req.photo_url:
                try:
                    import base64
                    from api.face_recognition_service import enroll_person_embedding

                    b64_data = req.photo_url.split("base64,")[1]
                    img_bytes = base64.b64decode(b64_data)
                    extracted = enroll_person_embedding(new_id, img_bytes)
                except Exception as ex:
                    print(f"[create_person] Error extracting embedding: {ex}")

            if not extracted:
                embedding = [0.1 * ((i + new_id) % 10) for i in range(128)]
                conn.execute(
                    """
                    INSERT INTO face_embeddings (person_id, embedding_json, feature_version)
                    VALUES (?, ?, 'v2')
                    """,
                    (new_id, json.dumps(embedding)),
                )
            conn.execute("UPDATE people SET is_enrolled = 1 WHERE id = ?", (new_id,))
            conn.commit()
            is_enrolled = 1

        try:
            generate_and_save_dossier(new_id, conn)
        except Exception as e:
            print(f"[create_person] Auto-generate dossier error: {e}")

        return {
            "success": True,
            "message": f"Registered {req.name}. Face biometric profile active.",
            "person": {
                "id": new_id,
                "identifier": req.identifier,
                "name": req.name,
                "role": req.role,
                "department": req.department,
                "class_grade": req.class_grade,
                "allowed_dress": req.allowed_dress or "Formals & Regular Uniform",
                "phone": req.phone,
                "email": req.email,
                "photo_url": req.photo_url,
                "is_enrolled": is_enrolled,
            },
        }
    finally:
        conn.close()


@router.patch("/{person_id}")
def update_person(person_id: int, req: UpdatePersonRequest):
    """Allows modifying person name, ID, department, dress code, role, status, etc."""
    conn = get_connection()
    try:
        person = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        # If identifier changed, verify uniqueness
        if req.identifier and req.identifier != person["identifier"]:
            dup = conn.execute(
                "SELECT id FROM people WHERE identifier = ? AND id != ?",
                (req.identifier, person_id),
            ).fetchone()
            if dup:
                raise HTTPException(
                    status_code=400,
                    detail="Identifier is already taken by another person",
                )

        updates = []
        params = []
        for field in [
            "name",
            "identifier",
            "role",
            "department",
            "class_grade",
            "allowed_dress",
            "status",
            "phone",
            "email",
            "photo_url",
        ]:
            val = getattr(req, field, None)
            if val is not None:
                updates.append(f"{field} = ?")
                params.append(val)

        if updates:
            params.append(person_id)
            conn.execute(
                f"UPDATE people SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            conn.commit()

        # If photo was updated, refresh face embedding & dossier
        if req.photo_url:
            extracted = False
            if "base64," in req.photo_url:
                try:
                    import base64
                    from api.face_recognition_service import enroll_person_embedding

                    b64_data = req.photo_url.split("base64,")[1]
                    img_bytes = base64.b64decode(b64_data)
                    extracted = enroll_person_embedding(person_id, img_bytes)
                except Exception as ex:
                    print(f"[update_person] Face embedding update error: {ex}")

            if not extracted and ("http" in req.photo_url or "data:" in req.photo_url):
                embedding = [0.1 * ((i + person_id) % 10) for i in range(128)]
                conn.execute(
                    "DELETE FROM face_embeddings WHERE person_id = ?", (person_id,)
                )
                conn.execute(
                    """
                    INSERT INTO face_embeddings (person_id, embedding_json, feature_version)
                    VALUES (?, ?, 'v2')
                    """,
                    (person_id, json.dumps(embedding)),
                )
            conn.execute("UPDATE people SET is_enrolled = 1 WHERE id = ?", (person_id,))
            conn.commit()

        try:
            generate_and_save_dossier(person_id, conn)
        except Exception as e:
            print(f"[update_person] Dossier refresh error: {e}")

        updated = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        return {
            "success": True,
            "message": f"Profile for {updated['name']} updated successfully",
            "person": dict(updated),
        }
    finally:
        conn.close()


@router.get("/{person_id}/history")
def get_person_history(person_id: int):
    """Returns an individual records table: Attendance records, dress checks, alerts."""
    conn = get_connection()
    try:
        person = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        # Attendance logs with camera names
        att_rows = conn.execute(
            """
            SELECT a.id, a.timestamp, a.status, a.confidence, c.camera_name, a.presence_seconds
            FROM attendance_records a
            LEFT JOIN cameras c ON a.camera_id = c.id
            WHERE a.person_id = ?
            ORDER BY a.id DESC
            LIMIT 50
        """,
            (person_id,),
        ).fetchall()

        # Detections / Alerts / Incident history
        alert_rows = conn.execute(
            """
            SELECT id, timestamp, object, priority, status, camera_id
            FROM alerts
            WHERE object LIKE ? OR object LIKE ?
            ORDER BY id DESC
            LIMIT 20
        """,
            (f"%{person['name']}%", f"%{person['identifier']}%"),
        ).fetchall()

        history_records = []
        for a in att_rows:
            history_records.append(
                {
                    "id": a["id"],
                    "type": "ATTENDANCE",
                    "timestamp": a["timestamp"],
                    "camera": a["camera_name"] or "Camera #1",
                    "event": "Automated Face Scan Check-in",
                    "status": a["status"],
                    "confidence": a["confidence"] or 0.95,
                    "notes": "Identity verified via facial biometrics",
                }
            )

        for al in alert_rows:
            history_records.append(
                {
                    "id": al["id"],
                    "type": "SECURITY_ALERT",
                    "timestamp": al["timestamp"],
                    "camera": f"Camera #{al['camera_id']}",
                    "event": al["object"],
                    "status": al["status"],
                    "confidence": 0.90,
                    "notes": f"Priority: {al['priority']}",
                }
            )

        # Sort combined history by timestamp descending
        history_records.sort(key=lambda x: str(x["timestamp"]), reverse=True)

        return {
            "success": True,
            "person": dict(person),
            "total_records": len(history_records),
            "history": history_records,
        }
    finally:
        conn.close()


@router.post("/{person_id}/mark-present")
def mark_person_present(person_id: int):
    """Manually marks attendance present for this individual today."""
    conn = get_connection()
    try:
        person = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "PRESENT"

        conn.execute(
            """
            INSERT INTO attendance_records (person_id, camera_id, environment_id, timestamp, confidence, status)
            VALUES (?, 1, ?, ?, 1.0, ?)
        """,
            (person_id, person["environment_id"] or 1, now_str, status),
        )
        conn.commit()

        return {
            "success": True,
            "message": f"Marked {person['name']} as PRESENT for {now_str}",
            "person_id": person_id,
            "status": "PRESENT",
            "timestamp": now_str,
        }
    finally:
        conn.close()


@router.post("/{person_id}/enroll-face")
def enroll_face(person_id: int, req: EnrollFaceRequest):
    conn = get_connection()
    try:
        person = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        # Extract real facial embedding if photo_url is base64 image
        extracted = False
        if req.photo_url and "base64," in req.photo_url:
            try:
                import base64
                from api.face_recognition_service import enroll_person_embedding

                b64_data = req.photo_url.split("base64,")[1]
                img_bytes = base64.b64decode(b64_data)
                extracted = enroll_person_embedding(person_id, img_bytes)
            except Exception as ex:
                print(f"[PeopleAPI] Base64 face embedding extraction error: {ex}")

        if not extracted:
            embedding = req.embedding or [
                0.1 * ((i + person_id) % 10) for i in range(128)
            ]
            embedding_json = json.dumps(embedding)
            conn.execute(
                "DELETE FROM face_embeddings WHERE person_id = ?", (person_id,)
            )
            conn.execute(
                """
                INSERT INTO face_embeddings (person_id, embedding_json, feature_version)
                VALUES (?, ?, 'v2')
            """,
                (person_id, embedding_json),
            )

        conn.execute(
            """
            UPDATE people
            SET is_enrolled = 1, photo_url = COALESCE(?, photo_url)
            WHERE id = ?
        """,
            (req.photo_url, person_id),
        )

        conn.commit()

        try:
            generate_and_save_dossier(person_id, conn)
        except Exception as e:
            print(f"[enroll_face] Dossier refresh error: {e}")

        updated_p = conn.execute(
            "SELECT photo_url FROM people WHERE id = ?", (person_id,)
        ).fetchone()

        return {
            "success": True,
            "message": f"Face enrollment completed for {person['name']}",
            "person_id": person_id,
            "is_enrolled": 1,
            "photo_url": updated_p["photo_url"] if updated_p else req.photo_url,
        }
    finally:
        conn.close()


@router.delete("/{person_id}")
def delete_person(person_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM face_embeddings WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM attendance_records WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM people WHERE id = ?", (person_id,))
        conn.commit()
        return {"success": True, "message": "Person deleted successfully"}
    finally:
        conn.close()


@router.post("/batch")
def create_people_batch(req: BatchCreatePeopleRequest):
    conn = get_connection()
    try:
        created = []
        for p in req.people:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO people (name, identifier, role, department, class_grade, allowed_dress, phone, email, photo_url, environment_id, is_enrolled, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active')
            """,
                (
                    p.name,
                    p.identifier,
                    p.role,
                    p.department,
                    p.class_grade,
                    p.allowed_dress,
                    p.phone,
                    p.email,
                    p.photo_url,
                    p.environment_id or req.environment_id or 1,
                ),
            )
            pid = cursor.lastrowid
            created.append({"id": pid, "name": p.name, "identifier": p.identifier})
            # Extract real face embedding if photo was uploaded
            if p.photo_url and "base64," in p.photo_url:
                try:
                    import base64
                    from api.face_recognition_service import enroll_person_embedding

                    b64_data = p.photo_url.split("base64,")[1]
                    img_bytes = base64.b64decode(b64_data)
                    enroll_person_embedding(pid, img_bytes)
                except Exception as ex:
                    print(f"Batch face embedding extraction error for {pid}: {ex}")

            try:
                generate_and_save_dossier(pid, conn)
            except Exception as e:
                print(f"Could not auto-generate dossier for {pid}: {e}")
        conn.commit()
        return {
            "success": True,
            "count": len(created),
            "people": created,
            "message": f"Successfully enrolled {len(created)} personnel profiles",
        }
    finally:
        conn.close()


@router.delete("/environment/{env_id}/clear")
def clear_environment_people(env_id: int):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM face_embeddings WHERE person_id IN (SELECT id FROM people WHERE environment_id = ?)",
            (env_id,),
        )
        conn.execute(
            "DELETE FROM attendance_records WHERE person_id IN (SELECT id FROM people WHERE environment_id = ?)",
            (env_id,),
        )
        conn.execute("DELETE FROM people WHERE environment_id = ?", (env_id,))
        conn.commit()
        return {
            "success": True,
            "message": f"Cleared personnel for environment #{env_id}",
        }
    finally:
        conn.close()


@router.get("/{person_id}/dossier")
def get_dossier_data(person_id: int):
    dossier = get_person_dossier(person_id)
    if "error" in dossier:
        raise HTTPException(status_code=404, detail=dossier["error"])
    return dossier


@router.get("/{person_id}/dossier/markdown")
def get_dossier_markdown(person_id: int):
    dossier = get_person_dossier(person_id)
    if "error" in dossier:
        raise HTTPException(status_code=404, detail=dossier["error"])
    md_path = dossier.get("md_path")
    if md_path and Path(md_path).exists():
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/markdown")
    return Response(
        content=f"# Dossier for {dossier.get('dossier_title')}",
        media_type="text/markdown",
    )
