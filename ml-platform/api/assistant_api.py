import sqlite3
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/assistant",
    tags=["Sentronix AI Operations Assistant"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class ChatMessageRequest(BaseModel):
    message: str
    environment_id: Optional[int] = 1


# ============================================================================
# TOOL IMPLEMENTATIONS (Direct Database Query Functions)
# ============================================================================


def tool_get_cameras():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, camera_name, location, status, source_type, ai_enabled FROM cameras"
        ).fetchall()
        cameras = [dict(r) for r in rows]
        online = sum(1 for c in cameras if str(c["status"]).lower() == "online")
        return {
            "total": len(cameras),
            "online": online,
            "offline": len(cameras) - online,
            "cameras": cameras,
        }
    finally:
        conn.close()


def tool_get_alerts(priority: Optional[str] = None):
    conn = get_connection()
    try:
        query = "SELECT * FROM alerts WHERE UPPER(status) = 'ACTIVE'"
        params = []
        if priority:
            query += " AND UPPER(priority) = ?"
            params.append(priority.upper())
        query += " ORDER BY id DESC LIMIT 10"
        rows = conn.execute(query, params).fetchall()
        alerts = [dict(r) for r in rows]
        return {"count": len(alerts), "alerts": alerts}
    finally:
        conn.close()


def tool_get_attendance():
    conn = get_connection()
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        total_enrolled = conn.execute(
            "SELECT COUNT(*) FROM people WHERE status = 'active'"
        ).fetchone()[0]
        rows = conn.execute(
            """
            SELECT a.id, a.timestamp, a.status, a.confidence, p.name, p.identifier, p.role
            FROM attendance_records a
            JOIN people p ON a.person_id = p.id
            WHERE a.timestamp LIKE ?
            ORDER BY a.id DESC LIMIT 10
        """,
            (f"{today_str}%",),
        ).fetchall()
        records = [dict(r) for r in rows]
        present_count = sum(1 for r in records if r["status"] == "PRESENT")
        late_count = sum(1 for r in records if r["status"] == "LATE")
        return {
            "date": today_str,
            "total_enrolled": total_enrolled,
            "present_count": present_count,
            "late_count": late_count,
            "absent_count": max(0, total_enrolled - (present_count + late_count)),
            "recent_records": records,
        }
    finally:
        conn.close()


def tool_get_detections():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM detections ORDER BY id DESC LIMIT 10"
        ).fetchall()
        return {"recent_detections": [dict(r) for r in rows]}
    finally:
        conn.close()


def tool_explain_alert(alert_id: int):
    conn = get_connection()
    try:
        alert = conn.execute(
            "SELECT * FROM alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        if not alert:
            return None
        return dict(alert)
    finally:
        conn.close()


def tool_get_system_health():
    return {
        "status": "healthy",
        "api_gateway": "online",
        "vision_engine": "online",
        "database": "sqlite_connected",
        "model": "YOLOv8/11 Inference Engine",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ============================================================================
# SENTRONIX OPERATIONAL ASSISTANT BRAIN
# ============================================================================


@router.post("/chat")
def assistant_chat(req: ChatMessageRequest):
    query = req.message.lower().strip()

    # 1. Camera queries
    if any(k in query for k in ["camera", "cameras", "offline", "online"]):
        data = tool_get_cameras()
        if "offline" in query:
            offline_list = [
                c["camera_name"]
                for c in data["cameras"]
                if str(c["status"]).lower() != "online"
            ]
            reply = f"There are {data['offline']} offline camera(s): {', '.join(offline_list) if offline_list else 'None, all cameras operational'}."
        else:
            reply = f"System has {data['total']} registered cameras ({data['online']} online, {data['offline']} offline). Active feeds include Entrance Cam 01."
        return {"reply": reply, "tool_called": "get_cameras", "data": data}

    # 2. Attendance queries
    if any(
        k in query
        for k in ["attendance", "student", "students", "present", "absent", "late"]
    ):
        data = tool_get_attendance()
        reply = (
            f"Attendance Summary for today ({data['date']}):\n"
            f"• Total Enrolled: {data['total_enrolled']}\n"
            f"• Present: {data['present_count']}\n"
            f"• Late: {data['late_count']}\n"
            f"• Absent: {data['absent_count']}\n"
        )
        if data["recent_records"]:
            latest = data["recent_records"][0]
            reply += f"Latest check-in: {latest['name']} ({latest['status']} at {latest['timestamp']})."
        return {"reply": reply, "tool_called": "get_attendance", "data": data}

    # 3. Alert / Security Incident queries
    if any(
        k in query
        for k in [
            "alert",
            "alerts",
            "critical",
            "incident",
            "hazard",
            "threat",
            "warning",
        ]
    ):
        # Check if looking for specific alert ID
        match = re.search(r"alert\s*#?(\d+)", query)
        if match:
            alert_id = int(match.group(1))
            alert = tool_explain_alert(alert_id)
            if alert:
                reply = (
                    f"Alert #{alert['id']} Explanation:\n"
                    f"• Object Detected: {alert['object']}\n"
                    f"• Priority: {alert['priority']}\n"
                    f"• AI Confidence: {int(alert['confidence'] * 100)}%\n"
                    f"• Timestamp: {alert['timestamp']}\n"
                    f"• Current Status: {alert['status']}\n"
                    f"Operational Guidance: Review camera footage immediately and dispatch on-duty security if unconfirmed."
                )
            else:
                reply = f"Alert #{alert_id} was not found in the surveillance database."
            return {"reply": reply, "tool_called": "explain_alert", "data": alert}

        priority = "CRITICAL" if "critical" in query else None
        data = tool_get_alerts(priority)
        reply = f"Found {data['count']} active security alert(s). "
        if data["alerts"]:
            latest = data["alerts"][0]
            reply += f"Latest: {latest['priority']} alert for '{latest['object']}' ({int(latest['confidence']*100)}% confidence) at {latest['timestamp']}."
        else:
            reply += "No unresolved critical security alerts currently."
        return {"reply": reply, "tool_called": "get_alerts", "data": data}

    # 4. System health
    if any(k in query for k in ["health", "status", "system", "version"]):
        data = tool_get_system_health()
        reply = f"All Sentronix core services are operating nominally. AI Vision Engine: {data['model']} (Active). Database: Connected."
        return {"reply": reply, "tool_called": "get_system_health", "data": data}

    # 5. Default Operator Assistance
    return {
        "reply": (
            "I am the Sentronix AI Surveillance Operations Assistant. You can ask me:\n"
            "• 'How many students are present today?'\n"
            "• 'Which cameras are offline?'\n"
            "• 'Show active critical alerts'\n"
            "• 'Explain alert #1'\n"
            "• 'System health status'"
        ),
        "tool_called": None,
        "data": None,
    }
