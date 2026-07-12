@echo off
title AI Workstation Scheduler

echo ============================================
echo   AI Workstation Scheduler
echo ============================================
echo.

cd /d "%~dp0.."

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)

python -m app.scheduler
pause