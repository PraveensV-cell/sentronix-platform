"""
Sentronix AI — Universal Backend Launcher
==========================================
Run this from ANYWHERE:

    python sentronix_run.py            (from any directory)
    python D:\path\to\sentronix_run.py (absolute path also works)

This script automatically:
  1. Locates itself and the ml-platform directory
  2. Injects ml-platform into sys.path AND sets PYTHONPATH for child processes
  3. Initialises / migrates the database schema
  4. Starts Uvicorn on 0.0.0.0:8000 with hot-reload enabled
"""

import os
import sys
import subprocess
from pathlib import Path

# ── Resolve directories regardless of where this script is invoked from ──────
SCRIPT_DIR = Path(__file__).resolve().parent  # sentronix-platform/
ML_PLATFORM = SCRIPT_DIR / "ml-platform"
DATABASE_PY = ML_PLATFORM / "database" / "database_schema.py"
VENV_PYTHON = SCRIPT_DIR / ".venv" / "Scripts" / "python.exe"

# Choose interpreter: prefer .venv, fall back to the current interpreter
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

# ── Patch PYTHONPATH for this process AND all child processes ─────────────────
os.environ["PYTHONPATH"] = (
    str(ML_PLATFORM) + os.pathsep + os.environ.get("PYTHONPATH", "")
)
if str(ML_PLATFORM) not in sys.path:
    sys.path.insert(0, str(ML_PLATFORM))

print("=" * 60)
print("   SENTRONIX AI — Backend Launcher")
print("=" * 60)
print(f"  Project root : {SCRIPT_DIR}")
print(f"  ML platform  : {ML_PLATFORM}")
print(f"  Python       : {PYTHON}")
print("=" * 60)

# ── Step 1: Initialise / migrate the database ─────────────────────────────────
print("\n[1/2] Initialising database schema & camera fleet...")
result = subprocess.run([PYTHON, str(DATABASE_PY)], capture_output=True, text=True)
if result.returncode != 0:
    print("  WARNING:", result.stderr.strip())
else:
    print("  ✓ Database ready")

# ── Step 2: Start Uvicorn using --app-dir so the import 'api.main' works ─────
print("\n[2/2] Starting Uvicorn API server on http://0.0.0.0:8000 ...")
print("      Dashboard  → http://localhost:5173  (run run_frontend.bat separately)")
print("      API docs   → http://localhost:8000/docs\n")

subprocess.run(
    [
        PYTHON,
        "-m",
        "uvicorn",
        "api.main:app",
        "--app-dir",
        str(ML_PLATFORM),
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ],
    env=os.environ,
)
