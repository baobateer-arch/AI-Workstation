"""Claude Code Hook 接收器 - 处理 Claude Code 事件并更新 runtime 状态。"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.agent_runtime import update_agent_status
from app.core.state_manager import state_manager
from app.core.constants import AgentStatus
from app.core.event_bus import (
    event_bus,
    EVENT_SESSION_START,
    EVENT_TOOL_USE,
    EVENT_PERMISSION,
    EVENT_STOP,
)

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "claude_hook.log"

# Agent ID（VS Code 和 PowerShell Claude Code 暂时共用）
AGENT_ID = "claude_code_vscode"

# Agent 元数据
AGENT_NAME = "Claude Code"
AGENT_CHANNEL = "VS Code"

# 消息最大长度
MAX_MESSAGE_LENGTH = 300


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _log(event: str, data: dict[str, Any], error: str | None = None) -> None:
    """记录日志（安全：不记录敏感信息）"""
    _ensure_log_dir()
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event": event,
        "status": data.get("status", ""),
        "message": data.get("message", "")[:MAX_MESSAGE_LENGTH],
        "hook_event": data.get("hook_event", ""),
        "cwd": data.get("cwd", ""),
        "error": error,
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _truncate_message(msg: str) -> str:
    """截断消息到安全长度"""
    if len(msg) > MAX_MESSAGE_LENGTH:
        return msg[:MAX_MESSAGE_LENGTH] + "..."
    return msg


def _read_stdin() -> dict[str, Any]:
    """从标准输入读取 JSON"""
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            return {}
        return json.loads(input_data)
    except json.JSONDecodeError as e:
        _log("parse_error", {}, error=str(e))
        return {}
    except Exception as e:
        _log("read_error", {}, error=str(e))
        return {}


def handle_notification(data: dict[str, Any]) -> dict[str, Any]:
    """
    处理 Notification 事件。

    状态映射：
    - permission_prompt -> PERMISSION
    - idle_prompt -> WAITING
    - 其他 -> WAITING
    """
    notification_type = data.get("notification_type", "").lower()
    message = data.get("message", "")

    # 确定状态
    if "permission" in notification_type or "permission" in message.lower():
        status = "PERMISSION"
        status_msg = _truncate_message(message) if message else "等待授权"
    elif "idle" in notification_type or "waiting" in message.lower():
        status = "WAITING"
        status_msg = "等待用户回复"
    else:
        status = "WAITING"
        status_msg = _truncate_message(message) if message else "Claude Code 需要关注"

    result = {
        "status": status,
        "message": status_msg,
        "project": "",
        "hook_event": "notification",
        "session_id": data.get("session_id", ""),
        "cwd": data.get("cwd", ""),
        "source": "claude_hook",
    }

    return result


def handle_stop(data: dict[str, Any]) -> dict[str, Any]:
    """
    处理 Stop 事件。

    状态：DONE
    """
    return {
        "status": "DONE",
        "message": "任务完成，等待检查",
        "project": "",
        "hook_event": "stop",
        "session_id": data.get("session_id", ""),
        "cwd": data.get("cwd", ""),
        "source": "claude_hook",
    }


def handle_session_start(data: dict[str, Any]) -> dict[str, Any]:
    """
    处理 SessionStart 事件。

    状态：RUNNING
    """
    return {
        "status": "RUNNING",
        "message": "Claude Code 会话已开始",
        "project": "",
        "hook_event": "session_start",
        "session_id": data.get("session_id", ""),
        "cwd": data.get("cwd", ""),
        "source": "claude_hook",
    }


# 高风险工具列表（需要授权）
HIGH_RISK_TOOLS = {
    "bash",
    "shell",
    "delete",
    "write",
    "edit",
}


def handle_pre_tool_use(data: dict[str, Any]) -> dict[str, Any]:
    """
    处理 PreToolUse 事件。

    状态逻辑：
    - 高风险工具 -> PERMISSION
    - 其他工具 -> RUNNING

    message：只记录工具名称（不记录完整参数）
    """
    # 安全提取工具名称
    tool_name = data.get("tool_name", "") or data.get("tool", "") or data.get("name", "")
    if not tool_name:
        # 尝试从其他字段推断
        for key in ["tool_use", "tool_use_id", "function"]:
            if key in data:
                tool_name = str(data[key])[:50]
                break

    # 判断是否为高风险工具
    is_high_risk = tool_name.lower() in HIGH_RISK_TOOLS if tool_name else False

    # 构建状态和消息
    if is_high_risk:
        status = "PERMISSION"
        safe_msg = f"等待授权: {_truncate_message(tool_name)}"
    else:
        status = "RUNNING"
        if tool_name:
            safe_msg = f"执行工具: {_truncate_message(tool_name)}"
        else:
            safe_msg = "工具执行中"

    return {
        "status": status,
        "message": safe_msg,
        "project": "",
        "hook_event": "pre_tool_use",
        "session_id": data.get("session_id", ""),
        "cwd": data.get("cwd", ""),
        "source": "claude_hook",
    }


def process_event(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    处理事件并更新 runtime 状态。

    Args:
        event_type: 事件类型（notification/stop/session_start/pre_tool_use）
        data: 事件数据

    Returns:
        更新结果
    """
    # 事件处理映射
    handlers = {
        "notification": handle_notification,
        "stop": handle_stop,
        "session_start": handle_session_start,
        "pre_tool_use": handle_pre_tool_use,
    }

    handler = handlers.get(event_type.lower())
    if not handler:
        result = {
            "status": "WAITING",
            "message": f"未知事件: {event_type}",
            "hook_event": event_type,
        }
        _log("unknown_event", result)
        return result

    # 处理事件
    result = handler(data)

    # A. 更新旧版 agent_runtime.json（保持兼容）
    try:
        update_agent_status(
            agent_id=AGENT_ID,
            status=result["status"],
            message=result["message"],
            project=result.get("project", ""),
        )
    except Exception as e:
        _log("update_runtime_error", result, error=str(e))

    # B. 更新新版 workstation_state.json（使用统一的大写状态）
    try:
        state_manager.update_agent(
            agent_id=AGENT_ID,
            status=AgentStatus.normalize(result["status"]),
            message=result["message"],
            name=AGENT_NAME,
            channel=AGENT_CHANNEL,
            project=result.get("project", ""),
        )
    except Exception as e:
        _log("update_state_error", result, error=str(e))

    # C. 写入 EventBus（用于持久化和 Activity Tracker）
    try:
        # 映射事件类型
        event_mapping = {
            "session_start": EVENT_SESSION_START,
            "pre_tool_use": EVENT_TOOL_USE,
            "notification": EVENT_PERMISSION if result["status"] == "PERMISSION" else EVENT_TOOL_USE,
            "stop": EVENT_STOP,
        }
        ai_event = event_mapping.get(event_type, event_type)

        event_bus.emit(ai_event, {
            "agent": "claude",
            "status": result["status"],
            "hook_event": event_type,
        })
    except Exception as e:
        _log("event_bus_error", result, error=str(e))

    # 记录日志
    _log(event_type, result)

    return result


def try_refresh_dashboard() -> bool:
    """尝试刷新 dashboard（失败不影响主流程）"""
    try:
        from app.main import main as generate_dashboard
        generate_dashboard()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python -m app.hooks.claude_hook_handler <event_type>")
        print()
        print("事件类型:")
        print("  notification     通知事件")
        print("  stop             停止事件")
        print("  session_start    会话开始事件")
        print()
        print("输入: 从标准输入读取 JSON")
        sys.exit(1)

    event_type = sys.argv[1]

    # 读取输入数据
    data = _read_stdin()

    # 处理事件
    result = process_event(event_type, data)

    # 输出结果（供调试）
    print(json.dumps(result, ensure_ascii=False))

    # 尝试刷新 dashboard（可选，失败不影响）
    # try_refresh_dashboard()

    sys.exit(0)


if __name__ == "__main__":
    main()
