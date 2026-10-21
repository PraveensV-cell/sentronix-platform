@echo off
title Sentronix AI Backend
echo ============================================================
echo        SENTRONIX AI  -  Backend API Server
echo ============================================================
echo.

rem  Change to the directory where this .bat lives (project root)
cd /d "%~dp0"

rem  Use .venv python if present, otherwise fall back to system python
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo  Running from: %CD%
echo  Python      : %PY%
echo.

rem  Use the universal launcher — handles all path setup internally
%PY% sentronix_run.py

pause
