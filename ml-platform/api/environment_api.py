import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/environments",
    tags=["Environments & Modes"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class CreateEnvironmentRequest(BaseModel):
    name: str
    type: str  # School, College, Hospital, Industry, Office, Custom
    description: Optional[str] = None
    location: Optional[str] = None
    enabled_features: List[str]


class UpdateFeaturesRequest(BaseModel):
    enabled_features: List[str]


class UpdateEnvironmentRequest(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


@router.get("")
def list_environments():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM environments ORDER BY id ASC").fetchall()
        envs = []
        for r in rows:
            env_dict = dict(r)
            try:
                env_dict["enabled_features"] = (
                    json.loads(env_dict["enabled_features"])
                    if env_dict["enabled_features"]
                    else []
                )
            except Exception:
                env_dict["enabled_features"] = []
            envs.append(env_dict)
        return {"count": len(envs), "environments": envs}
    finally:
        conn.close()


@router.post("")
def create_environment(req: CreateEnvironmentRequest):
    conn = get_connection()
    try:
        features_json = json.dumps(req.enabled_features)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO environments (name, type, description, location, enabled_features, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """,
            (req.name, req.type, req.description, req.location, features_json),
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {
            "success": True,
            "message": "Environment created successfully",
            "environment": {
                "id": new_id,
                "name": req.name,
                "type": req.type,
                "description": req.description,
                "location": req.location,
                "enabled_features": req.enabled_features,
                "is_active": 1,
            },
        }
    finally:
        conn.close()


@router.get("/{env_id}")
def get_environment(env_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM environments WHERE id = ?", (env_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Environment not found")
        env_dict = dict(row)
        try:
            env_dict["enabled_features"] = (
                json.loads(env_dict["enabled_features"])
                if env_dict["enabled_features"]
                else []
            )
        except Exception:
            env_dict["enabled_features"] = []
        return {"success": True, "environment": env_dict}
    finally:
        conn.close()


@router.patch("/{env_id}")
def update_environment(env_id: int, req: UpdateEnvironmentRequest):
    """Allows renaming and modifying mode metadata."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM environments WHERE id = ?", (env_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Environment not found")

        updates = []
        params = []
        if req.name is not None:
            updates.append("name = ?")
            params.append(req.name)
        if req.type is not None:
            updates.append("type = ?")
            params.append(req.type)
        if req.description is not None:
            updates.append("description = ?")
            params.append(req.description)
        if req.location is not None:
            updates.append("location = ?")
            params.append(req.location)

        if updates:
            params.append(env_id)
            conn.execute(
                f"UPDATE environments SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )
            conn.commit()

        updated = conn.execute(
            "SELECT * FROM environments WHERE id = ?", (env_id,)
        ).fetchone()
        env_dict = dict(updated)
        try:
            env_dict["enabled_features"] = (
                json.loads(env_dict["enabled_features"])
                if env_dict["enabled_features"]
                else []
            )
        except Exception:
            env_dict["enabled_features"] = []

        return {
            "success": True,
            "message": "Environment updated successfully",
            "environment": env_dict,
        }
    finally:
        conn.close()


@router.patch("/{env_id}/features")
def update_environment_features(env_id: int, req: UpdateFeaturesRequest):
    conn = get_connection()
    try:
        features_json = json.dumps(req.enabled_features)
        conn.execute(
            """
            UPDATE environments
            SET enabled_features = ?
            WHERE id = ?
        """,
            (features_json, env_id),
        )
        conn.commit()
        return {
            "success": True,
            "message": "Environment features updated",
            "enabled_features": req.enabled_features,
        }
    finally:
        conn.close()
