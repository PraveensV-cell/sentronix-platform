import base64
import datetime
from pathlib import Path
from typing import List, Optional
import sqlite3

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.dossier_manager import (
    add_custom_file_to_person_folder,
    delete_file_from_person_folder,
    get_person_dossier,
    get_person_dossier_markdown,
    get_person_folder,
    get_person_folder_info,
    get_unknown_captures,
    get_unknown_folder,
    init_or_update_person_folder,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/people",
    tags=["People, Biometrics & VANTEP AI Dossiers"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class CreatePersonRequest(BaseModel):
    name: str
    identifier: str  # Student / Staff / Worker ID (e.g. STU-101)
    role: str = "student"  # student, staff, worker, officer, visitor
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
        raw_photo_bytes = None
        if req.photo_url and "base64," in req.photo_url:
            try:
                from api.face_recognition_service import enroll_person_embedding

                b64_data = req.photo_url.split("base64,")[1]
                raw_photo_bytes = base64.b64decode(b64_data)
                enroll_person_embedding(new_id, raw_photo_bytes)
            except Exception as ex:
                print(f"[create_person] Error extracting embedding: {ex}")

        # Initialize physical folder for this individual managed by VANTEP AI
        person_data = {
            "id": new_id,
            "environment_id": req.environment_id or 1,
            "name": req.name,
            "identifier": req.identifier,
            "role": req.role,
            "department": req.department,
            "class_grade": req.class_grade,
            "allowed_dress": req.allowed_dress,
            "phone": req.phone,
            "email": req.email,
            "photo_url": req.photo_url,
            "is_enrolled": 1 if raw_photo_bytes else 0,
        }
        init_or_update_person_folder(
            new_id,
            person_dict=person_data,
            photo_bytes=raw_photo_bytes,
            conn=conn,
        )

        return {
            "success": True,
            "id": new_id,
            "message": f"Enrolled {req.name} and initialized VANTEP AI dossier folder",
            "person": person_data,
        }
    finally:
        conn.close()


@router.patch("/{person_id}")
def update_person(person_id: int, req: UpdatePersonRequest):
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

        # If photo was updated, refresh face embedding
        raw_photo_bytes = None
        if req.photo_url and "base64," in req.photo_url:
            try:
                from api.face_recognition_service import enroll_person_embedding

                b64_data = req.photo_url.split("base64,")[1]
                raw_photo_bytes = base64.b64decode(b64_data)
                enroll_person_embedding(person_id, raw_photo_bytes)
                conn.execute(
                    "UPDATE people SET is_enrolled = 1 WHERE id = ?",
                    (person_id,),
                )
                conn.commit()
            except Exception as ex:
                print(f"[update_person] Face embedding update error: {ex}")

        updated = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        p_dict = dict(updated)

        # Update physical folder managed by VANTEP AI
        init_or_update_person_folder(
            person_id,
            person_dict=p_dict,
            photo_bytes=raw_photo_bytes,
            conn=conn,
        )

        return {
            "success": True,
            "message": f"Profile for {p_dict['name']} updated successfully",
            "person": p_dict,
        }
    finally:
        conn.close()


@router.delete("/{person_id}")
def delete_person(person_id: int):
    conn = get_connection()
    try:
        person = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if person:
            env_id = person["environment_id"] or 1
            folder = get_person_folder(env_id, person_id, person["name"])
            import shutil

            if folder.exists():
                shutil.rmtree(folder, ignore_errors=True)

        conn.execute("DELETE FROM face_embeddings WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM attendance_records WHERE person_id = ?", (person_id,))
        conn.execute("DELETE FROM people WHERE id = ?", (person_id,))
        conn.commit()
        return {
            "success": True,
            "message": "Person and physical dossier folder deleted successfully",
        }
    finally:
        conn.close()


# ─── VANTEP AI PHYSICAL DOSSIER & FOLDER API ─────────────────────────────────


@router.get("/{person_id}/folder")
def get_person_folder_api(person_id: int):
    """Returns full physical folder contents: profile, attendance records, violation records, and files."""
    info = get_person_folder_info(person_id)
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@router.post("/{person_id}/folder/files")
async def upload_file_to_person_folder(person_id: int, file: UploadFile = File(...)):
    """Allows controller to upload any custom file/document directly into the individual's folder."""
    contents = await file.read()
    res = add_custom_file_to_person_folder(person_id, file.filename, contents)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.get("/{person_id}/folder/files/{filename}")
def download_file_from_person_folder(person_id: int, filename: str):
    """Downloads or views a file from the individual's folder."""
    conn = get_connection()
    try:
        person = conn.execute(
            "SELECT * FROM people WHERE id = ?", (person_id,)
        ).fetchone()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")
        env_id = person["environment_id"] or 1
        folder = get_person_folder(env_id, person_id, person["name"])

        # Check in root or in snapshots
        target = folder / filename
        if not target.exists():
            target = folder / "snapshots" / filename
        if not target.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(path=str(target), filename=filename)
    finally:
        conn.close()


@router.delete("/{person_id}/folder/files/{filename}")
def delete_file_from_person_folder_api(person_id: int, filename: str):
    """Deletes a custom file from the individual's folder."""
    res = delete_file_from_person_folder(person_id, filename)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


# ─── UNKNOWN PERSONS CAPTURE REPOSITORY ──────────────────────────────────────


@router.get("/environment/{env_id}/unknowns")
def list_unknown_captures(env_id: int):
    """Returns all captured unidentified persons logged by VANTEP AI in attendance/surveillance mode."""
    records = get_unknown_captures(env_id)
    return {"count": len(records), "unknown_records": records}


@router.get("/environment/{env_id}/unknowns/{filename}")
def get_unknown_photo(env_id: int, filename: str):
    folder = get_unknown_folder(env_id)
    target = folder / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Unknown capture image not found")
    return FileResponse(path=str(target), filename=filename)


# ─── BATCH DATASET IMPORT ────────────────────────────────────────────────────


@router.post("/batch")
def create_people_batch(req: BatchCreatePeopleRequest):
    """Batch imports staff/students/workers dataset and creates physical folders for each individual."""
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
            raw_photo_bytes = None
            if p.photo_url and "base64," in p.photo_url:
                try:
                    from api.face_recognition_service import (
                        enroll_person_embedding,
                    )

                    b64_data = p.photo_url.split("base64,")[1]
                    raw_photo_bytes = base64.b64decode(b64_data)
                    enroll_person_embedding(pid, raw_photo_bytes)
                except Exception as ex:
                    print(f"Batch face embedding extraction error for {pid}: {ex}")

            # Initialize physical folder for each individual
            init_or_update_person_folder(
                pid,
                person_dict={
                    "id": pid,
                    "name": p.name,
                    "identifier": p.identifier,
                    "role": p.role,
                    "department": p.department,
                    "class_grade": p.class_grade,
                    "allowed_dress": p.allowed_dress,
                    "phone": p.phone,
                    "email": p.email,
                    "photo_url": p.photo_url,
                    "environment_id": p.environment_id or req.environment_id or 1,
                    "is_enrolled": 1 if raw_photo_bytes else 0,
                },
                photo_bytes=raw_photo_bytes,
                conn=conn,
            )

        conn.commit()
        return {
            "success": True,
            "count": len(created),
            "people": created,
            "message": f"Successfully enrolled {len(created)} personnel profiles with VANTEP AI dossiers",
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

        # Clean dossiers directory for this environment
        import shutil

        env_dossier_dir = BASE_DIR / "dossiers" / f"env_{env_id}"
        if env_dossier_dir.exists():
            shutil.rmtree(env_dossier_dir, ignore_errors=True)

        return {
            "success": True,
            "message": f"Cleared personnel and folders for environment #{env_id}",
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

        # Update physical attendance file
        from api.dossier_manager import record_person_attendance_file

        record_person_attendance_file(
            person_id,
            status="PRESENT",
            confidence=1.0,
            camera_name="Control Room Manual Check-in",
            location="Administrator Terminal",
        )

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

        raw_photo_bytes = None
        if req.photo_url and "base64," in req.photo_url:
            try:
                from api.face_recognition_service import enroll_person_embedding

                b64_data = req.photo_url.split("base64,")[1]
                raw_photo_bytes = base64.b64decode(b64_data)
                enroll_person_embedding(person_id, raw_photo_bytes)
            except Exception as ex:
                print(f"[PeopleAPI] Base64 face embedding extraction error: {ex}")

        conn.execute(
            """
            UPDATE people
            SET is_enrolled = 1, photo_url = COALESCE(?, photo_url)
            WHERE id = ?
            """,
            (req.photo_url, person_id),
        )
        conn.commit()

        # Refresh folder
        init_or_update_person_folder(
            person_id,
            person_dict=dict(person),
            photo_bytes=raw_photo_bytes,
            conn=conn,
        )

        return {
            "success": True,
            "message": f"Face enrollment completed for {person['name']}",
            "person_id": person_id,
            "is_enrolled": 1,
            "photo_url": req.photo_url,
        }
    finally:
        conn.close()


@router.get("/{person_id}/dossier")
def get_dossier_data(person_id: int):
    return get_person_dossier(person_id)


@router.get("/{person_id}/dossier/markdown")
def get_dossier_markdown(person_id: int):
    content = get_person_dossier_markdown(person_id)
    return Response(content=content, media_type="text/markdown")
