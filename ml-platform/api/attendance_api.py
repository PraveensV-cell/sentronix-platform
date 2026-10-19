import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance System"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class RecordAttendanceRequest(BaseModel):
    person_id: int
    camera_id: Optional[int] = 1
    confidence: float = 0.85
    presence_seconds: Optional[int] = 5
    evidence_snapshot: Optional[str] = None
    environment_id: Optional[int] = 1


@router.get("")
def get_attendance(
    attendance_date: Optional[str] = None,
    environment_id: Optional[int] = 1,
    limit: int = 100,
):
    conn = get_connection()
    try:
        query_date = attendance_date or date.today().strftime("%Y-%m-%d")

        query = """
            SELECT 
                a.id,
                a.timestamp,
                a.confidence,
                a.status,
                a.presence_seconds,
                a.evidence_snapshot,
                p.id as person_id,
                p.name as person_name,
                p.identifier,
                p.role,
                p.department,
                p.class_grade,
                p.photo_url,
                COALESCE(c.camera_name, 'Entrance Camera') as camera_name
            FROM attendance_records a
            JOIN people p ON a.person_id = p.id
            LEFT JOIN cameras c ON a.camera_id = c.id
            WHERE a.timestamp LIKE ? AND a.environment_id = ?
            ORDER BY a.id DESC
            LIMIT ?
        """
        rows = conn.execute(query, (f"{query_date}%", environment_id, limit)).fetchall()
        records = [dict(r) for r in rows]

        return {"date": query_date, "count": len(records), "attendance": records}
    finally:
        conn.close()


@router.post("/record")
def record_attendance(req: RecordAttendanceRequest):
    conn = get_connection()
    try:
        person = conn.execute(
            "SELECT * FROM people WHERE id = ?", (req.person_id,)
        ).fetchone()
        if not person:
            raise HTTPException(status_code=404, detail="Person not found")

        today_str = date.today().strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Duplicate suppression: Check if already marked present in the last 15 minutes or today
        existing = conn.execute(
            """
            SELECT * FROM attendance_records 
            WHERE person_id = ? AND timestamp LIKE ?
            ORDER BY id DESC LIMIT 1
        """,
            (req.person_id, f"{today_str}%"),
        ).fetchone()

        if existing:
            return {
                "success": False,
                "message": f"{person['name']} already marked present today at {existing['timestamp']}",
                "record": dict(existing),
                "is_duplicate": True,
            }

        # Determine if on time or late (e.g. after 09:00 is LATE)
        current_hour = datetime.now().hour
        status = "LATE" if current_hour >= 9 else "PRESENT"

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO attendance_records (
                person_id, camera_id, environment_id, timestamp, confidence, status, presence_seconds, evidence_snapshot
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                req.person_id,
                req.camera_id or 1,
                req.environment_id or 1,
                now_str,
                req.confidence,
                status,
                req.presence_seconds or 5,
                req.evidence_snapshot,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

        return {
            "success": True,
            "message": f"Attendance marked for {person['name']} ({status})",
            "record": {
                "id": new_id,
                "person_name": person["name"],
                "identifier": person["identifier"],
                "status": status,
                "timestamp": now_str,
                "confidence": req.confidence,
            },
        }
    finally:
        conn.close()


@router.get("/summary")
def get_attendance_summary(environment_id: Optional[int] = 1):
    conn = get_connection()
    try:
        today_str = date.today().strftime("%Y-%m-%d")

        # Total enrolled
        total_enrolled = conn.execute(
            "SELECT COUNT(*) FROM people WHERE environment_id = ? AND status = 'active'",
            (environment_id,),
        ).fetchone()[0]

        # Present today
        present_count = conn.execute(
            """
            SELECT COUNT(DISTINCT person_id) FROM attendance_records
            WHERE environment_id = ? AND timestamp LIKE ? AND status = 'PRESENT'
        """,
            (environment_id, f"{today_str}%"),
        ).fetchone()[0]

        # Late today
        late_count = conn.execute(
            """
            SELECT COUNT(DISTINCT person_id) FROM attendance_records
            WHERE environment_id = ? AND timestamp LIKE ? AND status = 'LATE'
        """,
            (environment_id, f"{today_str}%"),
        ).fetchone()[0]

        total_marked = present_count + late_count
        absent_count = max(0, total_enrolled - total_marked)
        attendance_rate = (
            round((total_marked / total_enrolled * 100), 1)
            if total_enrolled > 0
            else 0.0
        )

        return {
            "date": today_str,
            "total_enrolled": total_enrolled,
            "present_count": present_count,
            "late_count": late_count,
            "absent_count": absent_count,
            "attendance_rate": attendance_rate,
        }
    finally:
        conn.close()
