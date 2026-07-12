@echo off
title AI Workstation - Test Claude Hook
echo ============================================
echo   AI Workstation - Claude Hook 测试
echo ============================================
echo.

:: 清除旧状态
echo [0/4] 清除旧状态...
python -c "from app.agent_runtime import clear_all_statuses; clear_all_statuses()"
echo.

:: 测试 1: SessionStart
echo [1/4] 测试 SessionStart...
echo {"session_id":"test-session","cwd":"D:\\AIProjects\\AI-Workstation-Dashboard"} | python -m app.hooks.claude_hook_handler session_start
echo.

:: 测试 2: Notification permission_prompt
echo [2/4] 测试 Notification (permission_prompt)...
echo {"session_id":"test-session","cwd":"D:\\AIProjects\\AI-Workstation-Dashboard","notification_type":"permission_prompt","message":"Claude Code 请求执行：npm install"} | python -m app.hooks.claude_hook_handler notification
echo.

:: 测试 3: Notification idle_prompt
echo [3/4] 测试 Notification (idle_prompt)...
echo {"session_id":"test-session","notification_type":"idle_prompt","message":"Claude Code 正在等待用户输入"} | python -m app.hooks.claude_hook_handler notification
echo.

:: 测试 4: Stop
echo [4/4] 测试 Stop...
echo {"session_id":"test-session","cwd":"D:\\AIProjects\\AI-Workstation-Dashboard"} | python -m app.hooks.claude_hook_handler stop
echo.

:: 显示最终状态
echo ============================================
echo   Runtime 最终状态
echo ============================================
python -c "import json; print(json.dumps(json.load(open('data/agent_runtime.json','r',encoding='utf-8')),ensure_ascii=False,indent=2))"
echo.

pause
