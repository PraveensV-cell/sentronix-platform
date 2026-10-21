@echo off
title SENTRONIX AI — Backend Server
color 0A

echo.
echo  ============================================================
echo     SENTRONIX AI  -  Backend API Server
echo  ============================================================
echo.

rem ── Step 1: Switch to the project root (works from ANY directory) ──
cd /d "D:\majorproject\sentronix-platform"

if errorlevel 1 (
    echo  [ERROR] Cannot find D:\majorproject\sentronix-platform
    echo  Make sure the project folder exists at that path.
    pause
    exit /b 1
)

echo  [OK] Working directory: %CD%

rem ── Step 2: Select Python interpreter ──
if exist ".venv\Scripts\python.exe" (
    set "PY=D:\majorproject\sentronix-platform\.venv\Scripts\python.exe"
    echo  [OK] Using project Python: %PY%
) else (
    set "PY=python"
    echo  [OK] Using system Python
)

rem ── Step 3: Init database ──
echo.
echo  [1/2] Initialising database...
%PY% ml-platform\database\database_schema.py
echo  [OK] Database ready

rem ── Step 4: Start Uvicorn with correct --app-dir ──
echo.
echo  [2/2] Starting API server on http://localhost:8000 ...
echo        API Docs : http://localhost:8000/docs
echo.
%PY% -m uvicorn api.main:app --app-dir "D:\majorproject\sentronix-platform\ml-platform" --host 0.0.0.0 --port 8000 --reload

pause
