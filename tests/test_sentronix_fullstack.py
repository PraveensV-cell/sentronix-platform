import sys
import unittest
from pathlib import Path

# Add ml-platform to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_PLATFORM_DIR = PROJECT_ROOT / "ml-platform"
sys.path.insert(0, str(ML_PLATFORM_DIR))

from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402
from database.database_schema import (  # noqa: E402
    init_database,
    seed_default_environment_and_rules,
)


class TestSentronixFullStack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()
        seed_default_environment_and_rules()
        cls.client = TestClient(app)

    def test_01_root_and_status(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["ai"], "active")

    def test_02_auth_workflow(self):
        # Register new operator
        username = "test_guard_1"
        email = "guard1@school.edu"
        reg_res = self.client.post(
            "/auth/register",
            json={
                "username": username,
                "email": email,
                "full_name": "Campus Security Officer",
                "password": "Password123!",
                "role": "operator",
            },
        )
        self.assertEqual(reg_res.status_code, 200)
        otp = reg_res.json()["dev_mock_otp"]
        self.assertTrue(len(otp) == 6)

        # Verify OTP
        verify_res = self.client.post(
            "/auth/verify-otp", json={"email": email, "otp": otp}
        )
        self.assertEqual(verify_res.status_code, 200)

        # Login
        login_res = self.client.post(
            "/auth/login",
            json={"username_or_email": username, "password": "Password123!"},
        )
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access_token", login_res.json())

    def test_03_environments_and_features(self):
        res = self.client.get("/environments")
        self.assertEqual(res.status_code, 200)
        envs = res.json()["environments"]
        self.assertGreaterEqual(len(envs), 1)

        # Update features
        env_id = envs[0]["id"]
        patch_res = self.client.patch(
            f"/environments/{env_id}/features",
            json={
                "enabled_features": ["face_detection", "attendance", "alerts", "rules"]
            },
        )
        self.assertEqual(patch_res.status_code, 200)

    def test_04_camera_management(self):
        res = self.client.get("/cameras")
        self.assertEqual(res.status_code, 200)
        cameras = res.json()["cameras"]
        self.assertGreaterEqual(len(cameras), 1)

    def test_05_people_and_face_enrollment(self):
        identifier = "STU-999"
        create_res = self.client.post(
            "/people",
            json={
                "name": "Arjun Singhania",
                "identifier": identifier,
                "role": "student",
                "department": "Engineering",
                "class_grade": "Year 1",
            },
        )
        self.assertEqual(create_res.status_code, 200)
        person_id = create_res.json()["person"]["id"]

        # Enroll face
        enroll_res = self.client.post(f"/people/{person_id}/enroll-face", json={})
        self.assertEqual(enroll_res.status_code, 200)
        self.assertEqual(enroll_res.json()["is_enrolled"], 1)

    def test_06_attendance_and_deduplication(self):
        # Find enrolled student
        people_res = self.client.get("/people")
        person = people_res.json()["people"][0]

        # Record attendance
        att_res = self.client.post(
            "/attendance/record",
            json={"person_id": person["id"], "camera_id": 1, "confidence": 0.94},
        )
        self.assertEqual(att_res.status_code, 200)

        # Second call should recognize duplicate
        dup_res = self.client.post(
            "/attendance/record",
            json={"person_id": person["id"], "camera_id": 1, "confidence": 0.94},
        )
        self.assertTrue(dup_res.json().get("is_duplicate", False))

        # Check summary
        sum_res = self.client.get("/attendance/summary")
        self.assertEqual(sum_res.status_code, 200)
        self.assertGreaterEqual(
            sum_res.json()["present_count"] + sum_res.json()["late_count"], 1
        )

    def test_07_rules_engine(self):
        rules_res = self.client.get("/rules")
        self.assertEqual(rules_res.status_code, 200)
        rules = rules_res.json()["rules"]
        self.assertGreaterEqual(len(rules), 1)

        # Toggle rule
        rule_id = rules[0]["id"]
        toggle_res = self.client.patch(f"/rules/{rule_id}/toggle")
        self.assertEqual(toggle_res.status_code, 200)

    def test_08_alerts_and_resolution(self):
        alerts_res = self.client.get("/alerts")
        self.assertEqual(alerts_res.status_code, 200)
        alerts = alerts_res.json()["alerts"]
        if alerts:
            first_id = alerts[0]["id"]
            patch_res = self.client.patch(f"/alerts/{first_id}/status?status=RESOLVED")
            self.assertEqual(patch_res.status_code, 200)
            self.assertEqual(patch_res.json()["alert"]["status"], "RESOLVED")

    def test_09_ai_assistant_tool_execution(self):
        # Query attendance
        res1 = self.client.post(
            "/assistant/chat", json={"message": "How many students are present today?"}
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["tool_called"], "get_attendance")

        # Query cameras
        res2 = self.client.post(
            "/assistant/chat", json={"message": "Which cameras are offline?"}
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["tool_called"], "get_cameras")

        # Query alerts
        res3 = self.client.post(
            "/assistant/chat", json={"message": "Show critical alerts"}
        )
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(res3.json()["tool_called"], "get_alerts")


if __name__ == "__main__":
    unittest.main()
