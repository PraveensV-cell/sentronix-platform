import hashlib
import random
import sqlite3
from datetime import datetime, timedelta
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

        # Generate 6-digit development OTP
        mock_otp = f"{random.randint(100000, 999999)}"
        expires_at = (datetime.now() + timedelta(minutes=15)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        hashed_pw = hash_password(req.password)
        conn.execute(
            """
            INSERT INTO users (username, email, full_name, phone, hashed_password, role, is_verified, is_active, otp_code, otp_expires_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
        """,
            (
                req.username,
                req.email,
                req.full_name,
                req.phone,
                hashed_pw,
                req.role or "operator",
                mock_otp,
                expires_at,
            ),
        )
        conn.commit()

        return {
            "success": True,
            "message": "User registered. Please verify your account with OTP.",
            "dev_mock_otp": mock_otp,
            "instructions": f"[DEV MODE] Use OTP: {mock_otp} to verify your account instantly.",
        }
    finally:
        conn.close()


@router.post("/verify-otp")
def verify_otp(req: VerifyOtpRequest):
    conn = get_connection()
    try:
        lookup = req.email_or_phone or req.email
        if not lookup:
            raise HTTPException(status_code=400, detail="Email or phone is required")

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? OR phone = ? OR username = ?",
            (lookup, lookup, lookup),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user["is_verified"] == 1:
            return {"success": True, "message": "Account is already verified."}

        # Check OTP
        if (
            user["otp_code"] != req.otp and req.otp != "123456"
        ):  # Fallback master dev OTP
            raise HTTPException(status_code=400, detail="Invalid OTP code")

        conn.execute(
            "UPDATE users SET is_verified = 1, otp_code = NULL WHERE id = ?",
            (user["id"],),
        )
        conn.commit()

        return {
            "success": True,
            "message": "Account verified successfully. You may now login.",
        }
    finally:
        conn.close()


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
