import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/rules",
    tags=["Surveillance Rule Engine"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class CreateRuleRequest(BaseModel):
    name: str
    rule_type: str  # restricted_zone, prohibited_activity, dress_code, attendance, crowd_detection
    conditions: Dict[str, Any]
    severity: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    cooldown_seconds: int = 30
    environment_id: Optional[int] = 1


@router.get("")
def list_rules(environment_id: Optional[int] = 1):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM rules WHERE environment_id = ? ORDER BY id ASC",
            (environment_id,),
        ).fetchall()

        rules = []
        for r in rows:
            rule_dict = dict(r)
            try:
                rule_dict["conditions"] = (
                    json.loads(rule_dict["conditions_json"])
                    if rule_dict["conditions_json"]
                    else {}
                )
            except Exception:
                rule_dict["conditions"] = {}
            rules.append(rule_dict)

        return {"count": len(rules), "rules": rules}
    finally:
        conn.close()


@router.post("")
def create_rule(req: CreateRuleRequest):
    conn = get_connection()
    try:
        conditions_json = json.dumps(req.conditions)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO rules (environment_id, name, rule_type, conditions_json, severity, cooldown_seconds, is_enabled)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
            (
                req.environment_id or 1,
                req.name,
                req.rule_type,
                conditions_json,
                req.severity.upper(),
                req.cooldown_seconds,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

        return {
            "success": True,
            "message": "Security rule created successfully",
            "rule": {
                "id": new_id,
                "name": req.name,
                "rule_type": req.rule_type,
                "severity": req.severity.upper(),
                "conditions": req.conditions,
                "cooldown_seconds": req.cooldown_seconds,
                "is_enabled": 1,
            },
        }
    finally:
        conn.close()


@router.patch("/{rule_id}/toggle")
def toggle_rule(rule_id: int):
    conn = get_connection()
    try:
        rule = conn.execute(
            "SELECT is_enabled FROM rules WHERE id = ?", (rule_id,)
        ).fetchone()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        new_status = 0 if rule["is_enabled"] == 1 else 1
        conn.execute(
            "UPDATE rules SET is_enabled = ? WHERE id = ?", (new_status, rule_id)
        )
        conn.commit()

        return {
            "success": True,
            "rule_id": rule_id,
            "is_enabled": bool(new_status),
            "message": f"Rule is now {'Enabled' if new_status == 1 else 'Disabled'}",
        }
    finally:
        conn.close()


@router.delete("/{rule_id}")
def delete_rule(rule_id: int):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
        conn.commit()
        return {"success": True, "message": "Rule deleted"}
    finally:
        conn.close()
