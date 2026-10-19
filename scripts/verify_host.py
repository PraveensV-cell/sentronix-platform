#!/usr/bin/env python3
"""
Sentronix AI Platform — Pre-Flight Host Verification Script
Validates all backend dependencies, database tables, seed records, model weights, and frontend bundle.
Usage:
    python scripts/verify_host.py
"""

import sys
import sqlite3
from pathlib import Path

# Enable UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_PLATFORM = PROJECT_ROOT / "ml-platform"
DB_PATH = ML_PLATFORM / "database" / "sentronix.db"
FRONTEND_DIST = ML_PLATFORM / "dashboard" / "dist" / "index.html"


def print_status(component: str, ok: bool, details: str = ""):
    symbol = "[OK]" if ok else "[FAIL]"
    print(f" {symbol:<7} {component:<35} {details}")


def verify_python_packages():
    print("\n--- 1. Python Environment & Core Dependencies ---")
    packages = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("PyTorch", "torch"),
        ("OpenCV", "cv2"),
        ("Ultralytics YOLO", "ultralytics"),
        ("NumPy", "numpy"),
        ("Pydantic", "pydantic"),
        ("HTTPX", "httpx"),
    ]
    all_ok = True
    for label, pkg_name in packages:
        try:
            mod = __import__(pkg_name)
            ver = getattr(mod, "__version__", "installed")
            print_status(label, True, f"v{ver}")
        except ImportError as e:
            print_status(label, False, f"Missing: {e}")
            all_ok = False
    return all_ok


def verify_database():
    print("\n--- 2. Database Schema & Tables ---")
    if not DB_PATH.exists():
        print_status("Database File", False, f"Not found at {DB_PATH}")
        return False

    print_status(
        "Database File",
        True,
        f"Found: {DB_PATH.name} ({DB_PATH.stat().st_size / 1024:.1f} KB)",
    )
    required_tables = [
        "users",
        "environments",
        "cameras",
        "camera_groups",
        "people",
        "face_embeddings",
        "attendance_records",
        "rules",
        "events",
        "alerts",
        "detections",
        "notifications",
        "audit_logs",
    ]
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cursor.fetchall()}

    missing = [t for t in required_tables if t not in existing]
    if missing:
        print_status("Table Schema", False, f"Missing tables: {missing}")
        return False
    print_status(
        "Table Schema", True, f"All {len(required_tables)} relational tables intact"
    )

    # Verify seed data
    counts = {}
    for t in ["users", "environments", "cameras", "people", "rules"]:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        counts[t] = cursor.fetchone()[0]
    conn.close()

    print_status(
        "Seed Records",
        True,
        f"Users: {counts['users']}, Envs: {counts['environments']}, Cams: {counts['cameras']}, People: {counts['people']}, Rules: {counts['rules']}",
    )
    return True


def verify_model_weights():
    print("\n--- 3. Pretrained AI Model Weights (Git LFS) ---")
    weights_to_check = [
        (PROJECT_ROOT / "yolo11n.pt", 5.0),
        (PROJECT_ROOT / "yolo11s.pt", 18.0),
        (PROJECT_ROOT / "weights" / "clip" / "ViT-B-32.pt", 330.0),
        (
            PROJECT_ROOT
            / "runs"
            / "detect"
            / "yolo26n-dfire-2"
            / "weights"
            / "best.pt",
            5.0,
        ),
    ]
    all_ok = True
    for path, min_mb in weights_to_check:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            ok = size_mb >= (min_mb * 0.8)
            print_status(path.name, ok, f"{size_mb:.2f} MB ({path.parent.name})")
            if not ok:
                all_ok = False
        else:
            print_status(path.name, False, "File not found")
            all_ok = False
    return all_ok


def verify_frontend():
    print("\n--- 4. Frontend Command Center Bundle ---")
    if FRONTEND_DIST.exists():
        print_status(
            "Production Dist Bundle", True, f"Verified at {FRONTEND_DIST.parent}"
        )
        return True
    else:
        print_status(
            "Production Dist Bundle",
            False,
            "Run 'cd ml-platform/dashboard && npm run build'",
        )
        return False


def main():
    print("=" * 60)
    print(" SENTRONIX AI — PRE-FLIGHT HOST VERIFICATION")
    print("=" * 60)

    p_ok = verify_python_packages()
    d_ok = verify_database()
    m_ok = verify_model_weights()
    f_ok = verify_frontend()

    print("\n" + "=" * 60)
    if p_ok and d_ok and m_ok and f_ok:
        print(
            " \033[92m✓ PRE-FLIGHT CHECK PASSED: Host is 100% Ready for Production!\033[0m"
        )
        print("=" * 60)
        sys.exit(0)
    else:
        print(
            " \033[93m⚠ PRE-FLIGHT CHECK WARNING: Some items require attention above.\033[0m"
        )
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
