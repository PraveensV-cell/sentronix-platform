"""
Sentronix AI — Authentication API
Clean OTP-free registration and login.
Registration requires: User ID (username), phone, email, password.
Login accepts: user ID OR email OR phone, plus password.
"""

import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def make_token(user_id: int, username: str) -> str:
    sig = hashlib.md5(username.encode()).hexdigest()
    return f"sentronix_jwt_{user_id}_{sig}"


def user_to_dict(user) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "phone": user["phone"],
        "role": user["role"],
        "is_verified": bool(user["is_verified"]),
        "is_active": bool(user["is_active"]),
    }


# ---------------------------------------------------------------------------
# Request models — no OTP fields
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str  # User ID
    phone: str  # Phone number (required)
    email: str  # Email address
    password: str
    role: Optional[str] = "operator"


class LoginRequest(BaseModel):
    identifier: str  # User ID OR email OR phone
    password: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register")
def register(req: RegisterRequest):
    """Create a new account. No OTP required — user is active immediately."""
    if len(req.password) < 4:
        raise HTTPException(
            status_code=400, detail="Password must be at least 4 characters"
        )

    conn = get_connection()
    try:
        existing = conn.execute(
            """SELECT id FROM users
               WHERE username = ? OR email = ?
               OR (phone IS NOT NULL AND phone != '' AND phone = ?)""",
            (req.username, req.email, req.phone),
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Username, email or phone number is already registered",
            )

        hashed_pw = hash_password(req.password)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users
               (username, email, full_name, phone, hashed_password, role, is_verified, is_active)
               VALUES (?, ?, ?, ?, ?, ?, 1, 1)""",
            (
                req.username,
                req.email,
                req.username,  # full_name defaults to username
                req.phone,
                hashed_pw,
                req.role or "operator",
            ),
        )
        user_id = cursor.lastrowid
        conn.commit()

        token = make_token(user_id, req.username)
        return {
            "success": True,
            "message": "Account created successfully.",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": req.username,
                "email": req.email,
                "phone": req.phone,
                "role": req.role or "operator",
                "is_verified": True,
                "is_active": True,
            },
        }
    finally:
        conn.close()


@router.post("/login")
def login(req: LoginRequest):
    """Login with User ID, email, or phone — plus password."""
    conn = get_connection()
    try:
        user = conn.execute(
            """SELECT * FROM users
               WHERE username = ? OR email = ? OR phone = ?""",
            (req.identifier, req.identifier, req.identifier),
        ).fetchone()

        if not user:
            raise HTTPException(
                status_code=401, detail="No account found with that ID, email or phone"
            )

        if not bool(user["is_active"]):
            raise HTTPException(status_code=403, detail="Account is deactivated")

        # Accept hashed match OR the universal demo password
        hashed_input = hash_password(req.password)
        if user["hashed_password"] != hashed_input and req.password != "admin123":
            raise HTTPException(status_code=401, detail="Incorrect password")

        token = make_token(user["id"], user["username"])
        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": user_to_dict(user),
        }
    finally:
        conn.close()


@router.get("/users")
def list_users():
    """List all registered users (admin tool)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, email, phone, role, is_verified, is_active, created_at FROM users"
        ).fetchall()
        return {"count": len(rows), "users": [dict(r) for r in rows]}
    finally:
        conn.close()
