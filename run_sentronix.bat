@echo off
title Sentronix AI - Full Stack Launcher
echo ========================================================
echo        SENTRONIX AI SURVEILLANCE PLATFORM
echo ========================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXEC=.venv\Scripts\python.exe
) else (
    set PYTHON_EXEC=python
)

%PYTHON_EXEC% start_sentronix.py
pause
