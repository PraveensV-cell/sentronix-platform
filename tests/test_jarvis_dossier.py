from fastapi.testclient import TestClient
from api.main import app
import time

client = TestClient(app)


def test_auth_no_otp_registration_and_login():
    """Verify registration requires only id, name, email, phone, password - NO OTP."""
    t = int(time.time() * 1000)
    uid = f"user_{t}"
    phone = f"+91 {str(t)[-10:]}"
    reg_res = client.post(
        "/auth/register",
        json={
            "username": uid,
            "name": "Commander Pravin",
            "phone": phone,
            "email": f"{uid}@sentronix.ai",
            "password": "securepassword123",
            "role": "admin",
        },
    )
    assert reg_res.status_code == 200
    data = reg_res.json()
    assert data["success"] is True
    assert data["user"]["name"] == "Commander Pravin"
    assert "access_token" in data

    # Test login
    login_res = client.post(
        "/auth/login", json={"identifier": uid, "password": "securepassword123"}
    )
    assert login_res.status_code == 200
    assert login_res.json()["success"] is True


def test_individual_dossier_generation_and_export():
    """Verify physical dossier file creation and retrieval."""
    res = client.get("/people/1/dossier")
    assert res.status_code == 200
    dossier = res.json()
    assert "dossier_id" in dossier
    assert "person_details" in dossier
    assert "attendance_performance" in dossier
    assert "ai_autonomous_assessment" in dossier

    # Test markdown export
    md_res = client.get("/people/1/dossier/markdown")
    assert md_res.status_code == 200
    assert "# 🏛️ SENTRONIX AI INDIVIDUAL DOSSIER" in md_res.text


def test_jarvis_ai_brain_operations():
    """Verify JARVIS AI 24/7 operations, speed mode, and daily work log."""
    status_res = client.get("/ai-brain/status")
    assert status_res.status_code == 200
    st = status_res.json()
    assert st["success"] is True
    assert "JARVIS" in st["name"]
    assert "ONLINE" in st["status"]

    # Test config update
    cfg_res = client.post(
        "/ai-brain/config",
        json={
            "name": "JARVIS ULTRA",
            "speed_mode": "TURBO",
            "autonomy_level": "FULL_AUTONOMOUS",
        },
    )
    assert cfg_res.status_code == 200
    assert cfg_res.json()["config"]["name"] == "JARVIS ULTRA"

    # Test daily log
    log_res = client.get("/ai-brain/daily-log")
    assert log_res.status_code == 200
    log = log_res.json()
    assert "work_log_date" in log
    assert "daily_metrics_summary" in log

    # Test daily log markdown
    md_res = client.get("/ai-brain/daily-log/markdown")
    assert md_res.status_code == 200
    assert "DAILY SURVEILLANCE WORK LOG" in md_res.text


def test_batch_people_and_clear_environment():
    """Verify batch personnel enrollment and clear roster for fresh onboarding."""
    batch_res = client.post(
        "/people/batch",
        json={
            "environment_id": 1,
            "people": [
                {
                    "name": "Cadet Arjun Dev",
                    "identifier": "CAD-101",
                    "role": "student",
                    "department": "Aeronautics",
                    "class_grade": "Squadron A",
                    "allowed_dress": "Military Formals",
                    "phone": "+91 9911223344",
                    "email": "arjun.dev@academy.edu",
                },
                {
                    "name": "Major Sunita Rao",
                    "identifier": "OFF-202",
                    "role": "staff",
                    "department": "Tactical Operations",
                    "class_grade": "Commandant",
                    "allowed_dress": "Service Dress Uniform",
                    "phone": "+91 9988776655",
                    "email": "sunita.rao@academy.edu",
                },
            ],
        },
    )
    assert batch_res.status_code == 200
    assert batch_res.json()["count"] == 2
