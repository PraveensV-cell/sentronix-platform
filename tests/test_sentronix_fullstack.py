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
        import uuid

        uid = uuid.uuid4().hex[:6]
        # Register — no OTP. Fields: username (User ID), phone, email, password
        username = f"test_guard_{uid}"
        email = f"guard_{uid}@school.edu"
        phone = f"+91{uid}"
        reg_res = self.client.post(
            "/auth/register",
            json={
                "username": username,
                "phone": phone,
                "email": email,
                "password": "Password123!",
                "role": "operator",
            },
        )
        self.assertEqual(reg_res.status_code, 200)
        reg_data = reg_res.json()
        self.assertTrue(reg_data["success"])
        self.assertIn("access_token", reg_data)

        # Login — accepts username OR email OR phone via "identifier" field
        login_res = self.client.post(
            "/auth/login",
            json={"identifier": username, "password": "Password123!"},
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
        self.assertGreaterEqual(len(cameras), 80)

        # Test function catalog
        func_res = self.client.get("/cameras/functions/list")
        self.assertEqual(func_res.status_code, 200)
        self.assertGreaterEqual(len(func_res.json()["functions"]), 7)

        # Test function assignment
        patch_func = self.client.patch(
            "/cameras/1/function",
            json={"assigned_function": "PERIMETER_INTRUSION"},
        )
        self.assertEqual(patch_func.status_code, 200)
        self.assertEqual(patch_func.json()["assigned_function"], "PERIMETER_INTRUSION")

    def test_05_people_and_face_enrollment(self):
        import uuid

        uid = uuid.uuid4().hex[:6]
        identifier = f"STU-{uid}"
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

    def test_10_camera_streaming_and_mobile_upload(self):
        # 1. Test network info endpoint
        net_res = self.client.get("/stream/network-info")
        self.assertEqual(net_res.status_code, 200)
        data = net_res.json()
        self.assertIn("local_ip", data)
        self.assertIn("mobile_dashboard_url", data)

        # 2. Test status endpoint
        status_res = self.client.get("/stream")
        self.assertEqual(status_res.status_code, 200)

        # 3. Test mobile frame upload
        import cv2
        import numpy as np

        # Create a blank test image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode(".jpg", img)
        img_bytes = img_encoded.tobytes()

        upload_res = self.client.post(
            "/stream/1/upload-frame",
            files={"file": ("frame.jpg", img_bytes, "image/jpeg")},
        )
        self.assertEqual(upload_res.status_code, 200)
        self.assertTrue(upload_res.json()["success"])

        # Check camera 1 status reflects the mobile upload
        cam_stat = self.client.get("/stream/1/status")
        self.assertEqual(cam_stat.status_code, 200)
        self.assertTrue(cam_stat.json()["has_mobile_stream"])


if __name__ == "__main__":
    unittest.main()
