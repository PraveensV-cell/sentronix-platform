@echo off
TITLE Sentronix AI - Production Host Launcher
COLOR 0A

echo ============================================================
echo   SENTRONIX AI -- INTELLIGENT SURVEILLANCE COMMAND CENTER
echo   Production Host Initialization
echo ============================================================

REM 1. Pre-flight host verification
python scripts\verify_host.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Pre-flight verification failed. Please inspect logs above.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [1/2] Launching Sentronix AI Operations API on port 8000...
start "Sentronix API" cmd /k "python start_sentronix.py"

echo.
echo ============================================================
echo   SENTRONIX AI IS NOW HOSTED AND OPERATIONAL
echo   Command Center: http://localhost:5173
echo   Swagger Docs:   http://localhost:8000/docs
echo ============================================================
