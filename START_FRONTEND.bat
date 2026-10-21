@echo off
title SENTRONIX AI — Frontend Dashboard
color 0B

echo.
echo  ============================================================
echo     SENTRONIX AI  -  React Dashboard (Frontend)
echo  ============================================================
echo.

rem ── Switch to dashboard folder (works from ANY directory) ──
cd /d "D:\majorproject\sentronix-platform\ml-platform\dashboard"

if errorlevel 1 (
    echo  [ERROR] Cannot find dashboard folder.
    pause
    exit /b 1
)

echo  [OK] Working directory: %CD%
echo.
echo  Starting dashboard on http://localhost:5173 ...
echo  (Open this URL in Chrome after the server starts)
echo.

npm run dev -- --host 0.0.0.0

pause
