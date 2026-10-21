@echo off
title Sentronix AI - Core Backend Server
echo ========================================================
echo        SENTRONIX AI — CORE VISION & API BACKEND
echo ========================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXEC=.venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

set PYTHONPATH=%~dp0ml-platform;%PYTHONPATH%

echo Initializing database schema & 80 cameras fleet...
%PYTHON_EXEC% ml-platform/database/database_schema.py

echo Starting Uvicorn API on http://0.0.0.0:8000 ...
%PYTHON_EXEC% -m uvicorn api.main:app --app-dir "%~dp0ml-platform" --host 0.0.0.0 --port 8000 --reload
pause
