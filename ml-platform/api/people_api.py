import json
import sqlite3
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException
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
    department: Optional[str] = None
    class_grade: Optional[str] = None
    photo_url: Optional[str] = None
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
        if role:
            query += " AND role = ?"
            params.append(role)
        query += " ORDER BY id DESC"

        rows = conn.execute(query, params).fetchall()
        people = [dict(r) for r in rows]

        # Check today's attendance for each person
        import datetime

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
            INSERT INTO people (environment_id, identifier, name, role, department, class_grade, photo_url, is_enrolled, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'active')
        """,
            (
                req.environment_id or 1,
                req.identifier,
                req.name,
                req.role,
                req.department,
                req.class_grade,
                req.photo_url,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

        return {
            "success": True,
            "message": "Person registered. Proceed to face enrollment.",
            "person": {
                "id": new_id,
                "identifier": req.identifier,
                "name": req.name,
                "role": req.role,
                "department": req.department,
                "class_grade": req.class_grade,
                "is_enrolled": 0,
            },
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

        # Store simulated embedding vector (128-dim or custom) if not provided
        embedding = req.embedding or [0.1 * ((i + person_id) % 10) for i in range(128)]
        embedding_json = json.dumps(embedding)

        conn.execute(
            """
            INSERT INTO face_embeddings (person_id, embedding_json, feature_version)
            VALUES (?, ?, 'v1')
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

        return {
            "success": True,
            "message": f"Face enrollment completed for {person['name']}",
            "person_id": person_id,
            "is_enrolled": 1,
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
