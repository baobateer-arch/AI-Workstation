@echo off
title AI Workstation - Uninstall Claude Hooks
echo ============================================
echo   AI Workstation - Claude Hooks 卸载器
echo ============================================
echo.

:: 检查 Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

echo [1/2] Dry-run 预览...
echo.
python -m app.hooks.install_claude_hooks uninstall --dry-run
echo.

echo ============================================
echo   请检查以上内容
echo ============================================
echo.
set /p confirm="确认卸载 Hooks? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo [INFO] 已取消卸载
    pause
    exit /b 0
)

echo.
echo [2/2] 卸载...
python -m app.hooks.install_claude_hooks uninstall
echo.

echo ============================================
echo   卸载完成
echo ============================================
pause
