import datetime
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"
DAILY_LOGS_DIR = BASE_DIR / "daily_logs"
START_TIME = time.time()

router = APIRouter(
    prefix="/ai-brain",
    tags=["VANTEP AI Main Brain & 24/7 Operations"],
)

# Global VANTEP AI Brain State
_ai_config = {
    "name": "VANTEP (JARVIS Series AI)",
    "codename": "JARVIS Class Autonomous Intelligence",
    "speed_mode": "HIGH_PRECISION",  # "TURBO", "BALANCED", "HIGH_PRECISION"
    "autonomy_level": "FULL_AUTONOMOUS",  # "FULL_AUTONOMOUS", "SUPERVISED", "ADVISORY"
    "voice_announcements": True,
    "neural_threads": 8,
    "current_status": "ONLINE (24/7 SURVEILLANCE ACTIVE)",
}

# Live Action Stream
_recent_actions: List[Dict[str, Any]] = [
    {
        "id": 1,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "module": "VANTEP_SUPERVISOR",
        "action": "VANTEP AI 24/7 Neural Surveillance Engine active. Monitoring cameras, attendance, dress code, safety, and violations.",
        "severity": "INFO",
    }
]


def get_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_daily_log_dir() -> Path:
    DAILY_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return DAILY_LOGS_DIR


class AIConfigRequest(BaseModel):
    name: Optional[str] = None
    speed_mode: Optional[str] = None
    autonomy_level: Optional[str] = None
    voice_announcements: Optional[bool] = None


class LogActionRequest(BaseModel):
    module: str
    action: str
    severity: Optional[str] = "INFO"
    metadata: Optional[Dict[str, Any]] = None


def generate_daily_work_log(today_date: Optional[str] = None) -> Dict[str, Any]:
    if not today_date:
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    try:
        att_count = conn.execute(
            "SELECT COUNT(*) FROM attendance_records WHERE timestamp LIKE ?",
            (f"{today_date}%",),
        ).fetchone()[0]

        alerts_today = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE timestamp LIKE ?",
            (f"{today_date}%",),
        ).fetchone()[0]

        dress_violations = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE object LIKE '%DRESS CODE VIOLATION%' AND timestamp LIKE ?",
            (f"{today_date}%",),
        ).fetchone()[0]

        safety_violations = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE object LIKE '%SAFETY HAZARD%' AND timestamp LIKE ?",
            (f"{today_date}%",),
        ).fetchone()[0]

        security_violations = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE object LIKE '%SECURITY ALERT%' AND timestamp LIKE ?",
            (f"{today_date}%",),
        ).fetchone()[0]

        cam_count = conn.execute(
            "SELECT COUNT(*) FROM cameras WHERE ai_enabled = 1"
        ).fetchone()[0]

        people_count = conn.execute(
            "SELECT COUNT(*) FROM people WHERE status = 'active'"
        ).fetchone()[0]

        # Calculate uptime
        uptime_seconds = int(time.time() - START_TIME)
        hours, rem = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        log_data = {
            "work_log_date": today_date,
            "ai_manager": _ai_config["name"],
            "system_version": "Sentronix AI 3.0 Enterprise",
            "operational_status": "24/7 CONTINUOUSLY ACTIVE",
            "uptime": uptime_str,
            "speed_profile": _ai_config["speed_mode"],
            "autonomy_mode": _ai_config["autonomy_level"],
            "daily_metrics_summary": {
                "active_cameras_monitored": cam_count,
                "verified_identities_on_file": people_count,
                "attendances_marked_today": att_count,
                "dress_code_violations_logged": dress_violations,
                "safety_ppe_violations_logged": safety_violations,
                "critical_security_alerts": security_violations,
                "total_alerts_logged": alerts_today,
            },
            "recent_autonomous_actions": _recent_actions[-25:],
            "ai_self_assessment": (
                f"{_ai_config['name']} is operating continuously in real-time. "
                f"Currently monitoring {cam_count} assigned surveillance camera streams. "
                f"Face recognition, automated attendance, uniform compliance, and safety threat detection are operational."
            ),
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Persist daily files
        log_dir = ensure_daily_log_dir()
        json_file = log_dir / f"ai_work_log_{today_date}.json"
        md_file = log_dir / f"ai_work_log_{today_date}.md"

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)

        md_content = f"""# 🧠 {_ai_config['name'].upper()} — 24/7 DAILY SURVEILLANCE WORK LOG
**Date:** `{today_date}`  
**AI Manager & Supervisor:** `{_ai_config['name']}` ({_ai_config['codename']})  
**Operational Status:** `24/7 ONLINE & CONTINUOUSLY MONITORING`  
**Current Uptime:** `{uptime_str}`  
**Speed Profile:** `{_ai_config['speed_mode']}` | **Autonomy:** `{_ai_config['autonomy_level']}`

---

## 📊 Operational Telemetry
| Metric | Real Count | Status |
|--------|------------|--------|
| Active Cameras Monitored | {cam_count} | Active |
| Enrolled Biometric Profiles | {people_count} | Verified |
| Attendances Marked & Timestamped | {att_count} | Synced |
| Dress Code Violations Logged | {dress_violations} | Monitored |
| Safety & PPE Violations Logged | {safety_violations} | Monitored |
| Critical Security Alerts | {security_violations} | Intercepted |
| Total Active/Resolved Alerts | {alerts_today} | Managed |

---

## 🤖 VANTEP AI Executive Assessment
Subject monitoring and per-camera function enforcement active across all sectors. All individual folders and evidence snapshots synchronized.
"""
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        return log_data
    finally:
        conn.close()


@router.get("/status")
def get_ai_brain_status():
    """Returns real-time health and operational configuration of VANTEP AI."""
    uptime_seconds = int(time.time() - START_TIME)
    hours, rem = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    conn = get_db()
    try:
        active_cams = conn.execute(
            "SELECT COUNT(*) FROM cameras WHERE ai_enabled = 1"
        ).fetchone()[0]
        total_people = conn.execute(
            "SELECT COUNT(*) FROM people WHERE status = 'active'"
        ).fetchone()[0]
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        today_att = conn.execute(
            "SELECT COUNT(*) FROM attendance_records WHERE timestamp LIKE ?",
            (f"{today_str}%",),
        ).fetchone()[0]
        today_alerts = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE timestamp LIKE ?",
            (f"{today_str}%",),
        ).fetchone()[0]
    finally:
        conn.close()

    return {
        "success": True,
        "name": _ai_config["name"],
        "ai_name": _ai_config["name"],
        "status": _ai_config.get("current_status", "ONLINE_AND_MONITORING"),
        "codename": _ai_config["codename"],
        "speed_mode": _ai_config["speed_mode"],
        "autonomy_level": _ai_config["autonomy_level"],
        "voice_announcements": _ai_config["voice_announcements"],
        "neural_threads": _ai_config["neural_threads"],
        "current_status": _ai_config["current_status"],
        "uptime": uptime_str,
        "uptime_seconds": uptime_seconds,
        "active_cameras": active_cams,
        "enrolled_personnel": total_people,
        "today_attendance_count": today_att,
        "today_alerts_count": today_alerts,
        "last_heartbeat": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.post("/config")
def update_ai_config(req: AIConfigRequest):
    """Updates AI operational parameters (name, speed mode, autonomy, voice announcements)."""
    if req.name is not None:
        _ai_config["name"] = req.name.strip()
    if req.speed_mode is not None:
        _ai_config["speed_mode"] = req.speed_mode.upper()
    if req.autonomy_level is not None:
        _ai_config["autonomy_level"] = req.autonomy_level.upper()
    if req.voice_announcements is not None:
        _ai_config["voice_announcements"] = req.voice_announcements

    record_ai_action(
        module="SUPERVISOR",
        action=f"VANTEP AI parameters updated: Speed={_ai_config['speed_mode']}, Autonomy={_ai_config['autonomy_level']}.",
        severity="INFO",
    )

    return {
        "success": True,
        "message": "VANTEP AI configuration updated successfully",
        "config": _ai_config,
    }


@router.get("/daily-log")
def get_daily_work_log():
    return generate_daily_work_log()


@router.get("/daily-log/markdown")
def get_daily_work_log_markdown():
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    generate_daily_work_log(today_date)
    log_dir = ensure_daily_log_dir()
    md_file = log_dir / f"ai_work_log_{today_date}.md"
    if md_file.exists():
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/markdown")
    return Response(
        content="# VANTEP AI Daily Work Log Pending", media_type="text/markdown"
    )


@router.post("/action")
def log_ai_action_endpoint(req: LogActionRequest):
    return record_ai_action(req.module, req.action, req.severity, req.metadata)


@router.get("/actions")
def list_ai_actions(limit: int = 50):
    return {
        "count": len(_recent_actions),
        "actions": list(reversed(_recent_actions[-limit:])),
    }


def record_ai_action(
    module: str,
    action: str,
    severity: str = "INFO",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    act = {
        "id": len(_recent_actions) + 1,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "module": module,
        "action": action,
        "severity": severity,
        "metadata": metadata or {},
    }
    _recent_actions.append(act)
    if len(_recent_actions) > 200:
        _recent_actions.pop(0)
    return act


def record_ai_event(
    module: str,
    action: str,
    severity: str = "INFO",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compatibility alias for record_ai_action."""
    return record_ai_action(module, action, severity, metadata)
