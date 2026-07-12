@echo off
title AI Workstation Dashboard
echo ============================================
echo   AI Workstation Dashboard - v0.3
echo ============================================
echo.

:: Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.11+ and add to PATH.
    pause
    exit /b 1
)

echo [1/2] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [2/2] Generating images...
python -m app.main
echo.

if errorlevel 1 (
    echo [ERROR] Generation failed.
) else (
    echo 已生成：
    echo   output\dashboard.png
    echo   output\agent_status.png
)

echo.
pause
