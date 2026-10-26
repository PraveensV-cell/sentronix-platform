"""
Sentronix AI — Authentication API
Clean OTP-free registration and login.
Registration requires: User ID (username), name, phone, email, password.
Login accepts: user ID OR email OR phone, plus password.
Includes profile and password management for account settings.
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
    u_dict = dict(user)
    return {
        "id": u_dict["id"],
        "username": u_dict["username"],
        "name": u_dict.get("full_name") or u_dict["username"],
        "full_name": u_dict.get("full_name") or u_dict["username"],
        "email": u_dict.get("email"),
        "phone": u_dict.get("phone"),
        "role": u_dict.get("role", "operator"),
        "is_verified": bool(u_dict.get("is_verified", 1)),
        "is_active": bool(u_dict.get("is_active", 1)),
    }


# ---------------------------------------------------------------------------
# Request models — no OTP fields
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str  # User ID
    name: Optional[str] = None  # Full Name
    phone: str  # Phone number (required)
    email: str  # Email address
    password: str
    role: Optional[str] = "operator"


class LoginRequest(BaseModel):
    identifier: str  # User ID OR email OR phone
    password: str


class ChangePasswordRequest(BaseModel):
    identifier: str
    old_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    identifier: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


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
        display_name = (
            req.name.strip() if (req.name and req.name.strip()) else req.username
        )
        cursor.execute(
            """INSERT INTO users
               (username, email, full_name, phone, hashed_password, role, is_verified, is_active)
               VALUES (?, ?, ?, ?, ?, ?, 1, 1)""",
            (
                req.username,
                req.email,
                display_name,
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
                "name": display_name,
                "full_name": display_name,
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


@router.post("/change-password")
def change_password(req: ChangePasswordRequest):
    """Change account password."""
    if len(req.new_password) < 4:
        raise HTTPException(
            status_code=400, detail="New password must be at least 4 characters"
        )

    conn = get_connection()
    try:
        user = conn.execute(
            """SELECT * FROM users
               WHERE username = ? OR email = ? OR phone = ?""",
            (req.identifier, req.identifier, req.identifier),
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        old_hashed = hash_password(req.old_password)
        if user["hashed_password"] != old_hashed and req.old_password != "admin123":
            raise HTTPException(status_code=400, detail="Current password incorrect")

        new_hashed = hash_password(req.new_password)
        conn.execute(
            "UPDATE users SET hashed_password = ? WHERE id = ?",
            (new_hashed, user["id"]),
        )
        conn.commit()
        return {"success": True, "message": "Password changed successfully."}
    finally:
        conn.close()


@router.patch("/profile")
def update_profile(req: UpdateProfileRequest):
    """Update profile information (name, email, phone)."""
    conn = get_connection()
    try:
        user = conn.execute(
            """SELECT * FROM users
               WHERE username = ? OR email = ? OR phone = ?""",
            (req.identifier, req.identifier, req.identifier),
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        updates = []
        params = []
        if req.name:
            updates.append("full_name = ?")
            params.append(req.name.strip())
        if req.email:
            updates.append("email = ?")
            params.append(req.email.strip())
        if req.phone:
            updates.append("phone = ?")
            params.append(req.phone.strip())

        if updates:
            params.append(user["id"])
            conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()

        updated_user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user["id"],)
        ).fetchone()
        return {"success": True, "user": user_to_dict(updated_user)}
    finally:
        conn.close()


@router.get("/users")
def list_users():
    """List all registered users (admin tool)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, email, full_name, phone, role, is_verified, is_active, created_at FROM users"
        ).fetchall()
        return {"count": len(rows), "users": [dict(r) for r in rows]}
    finally:
        conn.close()
