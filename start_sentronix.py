import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)

DASHBOARD_DIR = ROOT_DIR / "ml-platform" / "dashboard"
ML_PLATFORM_DIR = ROOT_DIR / "ml-platform"


def main():
    print("=" * 60)
    print("   SENTRONIX AI — COMMAND CENTER LAUNCHER")
    print("=" * 60)
    print(f"Project Root: {ROOT_DIR}")
    print(f"Python Executable: {PYTHON_EXE}")

    # 1. Initialize and verify database
    print("\n[1/3] Initializing Relational Database & Seed Data...")
    db_schema_script = ML_PLATFORM_DIR / "database" / "database_schema.py"
    subprocess.run([str(PYTHON_EXE), str(db_schema_script)], check=True)

    # 2. Launch FastAPI Backend
    print("\n[2/3] Starting Sentronix Core API Backend on http://0.0.0.0:8000 ...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ML_PLATFORM_DIR)

    backend_proc = subprocess.Popen(
        [
            str(PYTHON_EXE),
            "-m",
            "uvicorn",
            "api.main:app",
            "--app-dir",
            str(ML_PLATFORM_DIR),
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        cwd=str(ML_PLATFORM_DIR),
        env=env,
    )

    time.sleep(2)

    # 3. Launch Vite Frontend
    print("\n[3/3] Starting React + Vite Command Center on http://localhost:5173 ...")
    frontend_proc = subprocess.Popen(
        [
            "npm.cmd" if os.name == "nt" else "npm",
            "run",
            "dev",
            "--",
            "--host",
            "0.0.0.0",
        ],
        cwd=str(DASHBOARD_DIR),
        shell=True,
    )

    time.sleep(3)
    target_url = "http://localhost:5173"
    print("\n" + "=" * 60)
    print("   SENTRONIX AI IS NOW RUNNING!")
    print(f"   Frontend UI:  {target_url}")
    print("   Backend API:  http://127.0.0.1:8000")
    print("   API Docs:     http://127.0.0.1:8000/docs")
    print("   Press Ctrl+C in this terminal to shutdown all services.")
    print("=" * 60)

    try:
        webbrowser.open(target_url)
    except Exception:
        pass

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down Sentronix services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Sentronix shutdown complete.")


if __name__ == "__main__":
    main()
