@echo off
title Sentronix AI - Command Center Dashboard
echo ========================================================
echo        SENTRONIX AI — COMMAND CENTER DASHBOARD
echo ========================================================
cd /d "%~dp0ml-platform\dashboard"

echo Starting Vite React Frontend on http://localhost:5173 ...
npm run dev -- --host 0.0.0.0
pause
