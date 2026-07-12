@echo off
chcp 65001 > nul
title AI Workstation Launcher

cd /d "%~dp0"

echo ===============================
echo   AI Workstation Starting...
echo ===============================

echo.
echo Starting Scheduler...
start "AI Scheduler" cmd /k python -m app.scheduler

timeout /t 3 > nul

echo Starting Kindle Server...
start "Kindle Server" cmd /k python -m app.kindle_server

echo.
echo AI Workstation Started
pause