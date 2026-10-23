import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras Fleet"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    return connection


class CreateCameraRequest(BaseModel):
    name: str
    location: Optional[str] = "Main Facility"
    zone: Optional[str] = "General"
    source_type: Optional[str] = "webcam"
    source_url: Optional[str] = "0"
    assigned_function: Optional[str] = "FACE_ATTENDANCE"
    group_id: Optional[int] = 1
    environment_id: Optional[int] = 1


class UpdateFunctionRequest(BaseModel):
    assigned_function: str


class UpdateSourceRequest(BaseModel):
    source_type: str
    source_url: str
    location: Optional[str] = None
    zone: Optional[str] = None


CAMERA_FUNCTIONS = [
    {
        "id": "FACE_ATTENDANCE",
        "label": "Face Recognition & Automated Attendance",
        "icon": "🎓",
        "description": "Localizes human faces, performs neural identity matching against student/staff registry, and logs attendance check-ins. Flags unknown persons.",
    },
    {
        "id": "DRESS_CODE",
        "label": "Dress Code & School Uniform Verification",
        "icon": "👔",
        "description": "Enforces school/college dress code policy. Only formals and regular school uniforms are allowed; flags casual wear and infractions.",
    },
    {
        "id": "EXAM_MONITOR",
        "label": "Exam Hall Proctoring & Cheating Detection",
        "icon": "📝",
        "description": "Monitors examination halls, detects prohibited smartphone usage, collaboration, unauthorized materials, and suspicious movements.",
    },
    {
        "id": "PERIMETER_INTRUSION",
        "label": "Perimeter Intrusion & Tripwire Detection",
        "icon": "⛔",
        "description": "Monitors restricted outer fences and sterile corridors; triggers immediate critical intrusion alarms if personnel enter.",
    },
    {
        "id": "DRESS_CODE_PPE",
        "label": "Industrial PPE & Safety Gear Compliance",
        "icon": "🦺",
        "description": "Enforces hardhat, high-vis safety vest, and protective eyewear compliance in industrial workshops and construction zones.",
    },
    {
        "id": "FIRE_SMOKE_HAZARD",
        "label": "Fire, Smoke & Thermal Hazard Alert",
        "icon": "🔥",
        "description": "Detects real-time fire outbreaks, smoke accumulation, or thermal hazards using computer vision neural networks.",
    },
    {
        "id": "CROWD_LOITERING",
        "label": "Crowd Density & Loitering Prevention",
        "icon": "👥",
        "description": "Monitors hallway bottlenecks, public concourses, and loitering stagnation beyond configurable dwell thresholds.",
    },
    {
        "id": "WEAPON_VIOLENCE",
        "label": "Weapon Detection & Violence Alert",
        "icon": "🚨",
        "description": "Real-time identification of brandished weapons, knives, physical altercations, or aggressive violent behaviors.",
    },
    {
        "id": "ANPR_VEHICLES",
        "label": "Vehicle Access & ANPR License Plate",
        "icon": "🚗",
        "description": "Monitors ingress/egress boom barriers, weigh stations, and enforces authorized parking lot allocation.",
    },
]


@router.get("/functions/list")
def get_camera_functions_catalog():
    """Returns standard operational functions assignable to cameras."""
    return {
        "success": True,
        "functions": CAMERA_FUNCTIONS,
    }


@router.get("")
def get_cameras(
    environment_id: Optional[int] = None,
    group_id: Optional[int] = None,
    assigned_function: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Returns the fleet of cameras with filtering by sector/group, function, or name."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                c.id,
                c.environment_id,
                c.group_id,
                c.camera_name,
                c.source_type,
                c.source_url,
                c.location,
                c.zone,
                c.assigned_function,
                c.status,
                c.ai_enabled,
                c.processing_fps,
                c.created_at,
                g.name AS group_name
            FROM cameras c
            LEFT JOIN camera_groups g ON c.group_id = g.id
            WHERE 1=1
        """
        params = []

        if environment_id is not None:
            query += " AND c.environment_id = ?"
            params.append(environment_id)

        if group_id is not None:
            query += " AND c.group_id = ?"
            params.append(group_id)

        if assigned_function:
            query += " AND UPPER(c.assigned_function) = ?"
            params.append(assigned_function.upper())

        if search:
            query += " AND (LOWER(c.camera_name) LIKE ? OR LOWER(c.location) LIKE ? OR LOWER(c.zone) LIKE ?)"
            term = f"%{search.lower()}%"
            params.extend([term, term, term])

        query += " ORDER BY c.id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        cameras = [dict(r) for r in rows]

        # Total count
        count_query = "SELECT COUNT(*) FROM cameras WHERE 1=1"
        count_params = []
        if environment_id is not None:
            count_query += " AND environment_id = ?"
            count_params.append(environment_id)
        if group_id is not None:
            count_query += " AND group_id = ?"
            count_params.append(group_id)
        if assigned_function:
            count_query += " AND UPPER(assigned_function) = ?"
            count_params.append(assigned_function.upper())

        total = conn.execute(count_query, count_params).fetchone()[0]

        return {
            "count": len(cameras),
            "total": total,
            "cameras": cameras,
        }
    finally:
        conn.close()


@router.get("/{camera_id}")
def get_camera(camera_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT 
                c.*,
                g.name AS group_name
            FROM cameras c
            LEFT JOIN camera_groups g ON c.group_id = g.id
            WHERE c.id = ?
        """,
            (camera_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Camera not found")

        return {
            "success": True,
            "camera": dict(row),
        }
    finally:
        conn.close()


@router.post("")
def create_camera(req: CreateCameraRequest):
    """Registers a new surveillance camera in the fleet."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cameras (
                environment_id, group_id, camera_name, source_type, source_url, location, zone, assigned_function, status, ai_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'online', 1)
        """,
            (
                req.environment_id or 1,
                req.group_id or 1,
                req.name,
                req.source_type or "webcam",
                req.source_url or "0",
                req.location or "Facility Area",
                req.zone or "General",
                req.assigned_function or "FACE_ATTENDANCE",
            ),
        )
        cam_id = cursor.lastrowid
        conn.commit()

        row = conn.execute("SELECT * FROM cameras WHERE id = ?", (cam_id,)).fetchone()
        return {
            "success": True,
            "message": "Camera registered successfully",
            "camera": dict(row),
        }
    finally:
        conn.close()


@router.patch("/{camera_id}/function")
def assign_camera_function(camera_id: int, req: UpdateFunctionRequest):
    """Assigns an operational AI function to a specific camera."""
    valid_ids = [f["id"] for f in CAMERA_FUNCTIONS]
    func_upper = req.assigned_function.upper()
    if func_upper not in valid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid function. Must be one of: {', '.join(valid_ids)}",
        )

    conn = get_connection()
    try:
        cam = conn.execute(
            "SELECT id FROM cameras WHERE id = ?", (camera_id,)
        ).fetchone()
        if not cam:
            raise HTTPException(status_code=404, detail="Camera not found")

        conn.execute(
            "UPDATE cameras SET assigned_function = ? WHERE id = ?",
            (func_upper, camera_id),
        )
        conn.commit()

        return {
            "success": True,
            "message": f"Camera {camera_id} assigned function: {func_upper}",
            "camera_id": camera_id,
            "assigned_function": func_upper,
        }
    finally:
        conn.close()


@router.patch("/{camera_id}/source")
def assign_camera_source(camera_id: int, req: UpdateSourceRequest):
    """Assigns video hardware or stream source to a camera."""
    conn = get_connection()
    try:
        cam = conn.execute(
            "SELECT id FROM cameras WHERE id = ?", (camera_id,)
        ).fetchone()
        if not cam:
            raise HTTPException(status_code=404, detail="Camera not found")

        updates = ["source_type = ?", "source_url = ?"]
        params = [req.source_type, req.source_url]

        if req.location:
            updates.append("location = ?")
            params.append(req.location)
        if req.zone:
            updates.append("zone = ?")
            params.append(req.zone)

        params.append(camera_id)
        conn.execute(f"UPDATE cameras SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

        return {
            "success": True,
            "message": f"Camera {camera_id} source updated to {req.source_type} ({req.source_url})",
            "camera_id": camera_id,
        }
    finally:
        conn.close()


@router.patch("/{camera_id}/toggle-ai")
def toggle_camera_ai(camera_id: int):
    """Toggles AI perception processing on or off for this camera."""
    conn = get_connection()
    try:
        cam = conn.execute(
            "SELECT id, ai_enabled FROM cameras WHERE id = ?", (camera_id,)
        ).fetchone()
        if not cam:
            raise HTTPException(status_code=404, detail="Camera not found")

        new_status = 0 if cam["ai_enabled"] == 1 else 1
        conn.execute(
            "UPDATE cameras SET ai_enabled = ? WHERE id = ?",
            (new_status, camera_id),
        )
        conn.commit()

        return {
            "success": True,
            "camera_id": camera_id,
            "ai_enabled": new_status,
        }
    finally:
        conn.close()
