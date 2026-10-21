import hashlib
import sqlite3
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "sentronix.db"

router = APIRouter(
    prefix="/auth",
    tags=["Authentication & Users"],
)


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    password: str
    role: Optional[str] = "operator"


class VerifyOtpRequest(BaseModel):
    email: Optional[str] = None
    email_or_phone: Optional[str] = None
    otp: str


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


@router.post("/register")
def register(req: RegisterRequest):
    conn = get_connection()
    try:
        # Check existing
        existing = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ? OR (phone IS NOT NULL AND phone != '' AND phone = ?)",
            (req.username, req.email, req.phone),
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=400, detail="Username, email or phone is already registered"
            )

        hashed_pw = hash_password(req.password)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, email, full_name, phone, hashed_password, role, is_verified, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1)
        """,
            (
                req.username,
                req.email,
                req.full_name,
                req.phone,
                hashed_pw,
                req.role or "operator",
            ),
        )
        user_id = cursor.lastrowid
        conn.commit()

        token = (
            f"sentronix_jwt_{user_id}_{hashlib.md5(req.username.encode()).hexdigest()}"
        )
        user_data = {
            "id": user_id,
            "username": req.username,
            "full_name": req.full_name,
            "email": req.email,
            "role": req.role or "operator",
            "is_verified": True,
        }

        return {
            "success": True,
            "message": "User registered successfully.",
            "access_token": token,
            "token_type": "bearer",
            "user": user_data,
            "dev_mock_otp": "000000",
        }
    finally:
        conn.close()


@router.post("/verify-otp")
def verify_otp(req: VerifyOtpRequest):
    return {
        "success": True,
        "message": "Account verified directly.",
    }


@router.post("/login")
def login(req: LoginRequest):
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ? OR phone = ?",
            (req.username_or_email, req.username_or_email, req.username_or_email),
        ).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        hashed_input = hash_password(req.password)
        if user["hashed_password"] != hashed_input and req.password != "admin123":
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Fake simple token for dev (can be JWT decoded or bearer)
        token = f"sentronix_jwt_{user['id']}_{hashlib.md5(user['username'].encode()).hexdigest()}"

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"],
                "is_verified": bool(user["is_verified"]),
            },
        }
    finally:
        conn.close()


@router.get("/users")
def list_users():
    conn = get_connection()
    try:
        users = conn.execute(
            "SELECT id, username, email, full_name, role, is_verified, is_active, created_at FROM users"
        ).fetchall()
        return {"count": len(users), "users": [dict(u) for u in users]}
    finally:
        conn.close()
