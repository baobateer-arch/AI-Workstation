@echo off
title AI Workstation - Install Claude Hooks
echo ============================================
echo   AI Workstation - Claude Hooks 安装器
echo ============================================
echo.

:: 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo [1/3] Dry-run 预览...
echo.
python -m app.hooks.install_claude_hooks status
echo.
python -m app.hooks.install_claude_hooks install --dry-run
echo.

echo ============================================
echo   请检查以上内容
echo ============================================
echo.
set /p confirm="确认安装 Hooks? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo [INFO] 已取消安装
    pause
    exit /b 0
)

echo.
echo [2/3] 创建备份并安装...
python -m app.hooks.install_claude_hooks install
echo.

echo [3/3] 验证安装...
python -m app.hooks.install_claude_hooks status
echo.

echo ============================================
echo   安装完成
echo ============================================
pause
