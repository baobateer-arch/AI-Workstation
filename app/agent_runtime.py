"""Agent 运行时状态管理 - 持久化到 JSON 文件。"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


# 数据目录
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RUNTIME_FILE = DATA_DIR / "agent_runtime.json"

# Agent 元数据默认值
AGENT_METADATA = {
    "claude_code_vscode": {
        "name": "Claude Code",
        "channel": "VS Code",
        "agent_type": "claude",
    },
    "claude_code_powershell": {
        "name": "Claude Code",
        "channel": "PowerShell",
        "agent_type": "claude",
    },
    "codex_desktop": {
        "name": "Codex",
        "channel": "桌面端",
        "agent_type": "codex",
    },
    "mimo_code_vscode": {
        "name": "MiMo Code",
        "channel": "VS Code",
        "agent_type": "mimo",
    },
    "mimo_code_powershell": {
        "name": "MiMo Code",
        "channel": "PowerShell",
        "agent_type": "mimo",
    },
    "claude_desktop": {
        "name": "Claude",
        "channel": "桌面端",
        "agent_type": "claude",
    },
}


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_runtime() -> dict[str, Any]:
    """加载运行时状态"""
    _ensure_data_dir()
    if RUNTIME_FILE.exists():
        try:
            with open(RUNTIME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_runtime(data: dict[str, Any]) -> None:
    """保存运行时状态"""
    _ensure_data_dir()
    with open(RUNTIME_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_agent_metadata(agent_id: str) -> dict[str, Any]:
    """获取 Agent 元数据（带默认值）"""
    return AGENT_METADATA.get(agent_id, {
        "name": agent_id,
        "channel": "unknown",
        "agent_type": "unknown",
    })


def update_agent_status(
    agent_id: str,
    status: str,
    message: str = "",
    project: str | None = None,
    name: str | None = None,
    channel: str | None = None,
    agent_type: str | None = None,
) -> dict[str, Any]:
    """
    更新单个Agent状态并保存到文件。

    Args:
        agent_id: Agent标识符
        status: 状态（如 RUNNING, PERMISSION, ERROR 等）
        message: 状态消息
        project: 当前项目名称（可选）
        name: Agent名称（可选，默认从元数据获取）
        channel: 渠道/平台（可选，默认从元数据获取）
        agent_type: Agent类型（可选，默认从元数据获取）

    Returns:
        更新后的状态字典
    """
    runtime = _load_runtime()

    # 获取元数据
    metadata = _get_agent_metadata(agent_id)

    entry = {
        "name": name or metadata.get("name", agent_id),
        "channel": channel or metadata.get("channel", "unknown"),
        "agent_type": agent_type or metadata.get("agent_type", "unknown"),
        "status": status.upper(),
        "message": message,
        "project": project or "",
        "updated": datetime.now().isoformat(),
    }

    runtime[agent_id] = entry
    _save_runtime(runtime)

    return entry


def get_agent_status(agent_id: str) -> dict[str, Any] | None:
    """获取单个Agent的运行时状态"""
    runtime = _load_runtime()
    return runtime.get(agent_id)


def get_all_runtime_statuses() -> dict[str, dict[str, Any]]:
    """获取所有Agent的运行时状态"""
    return _load_runtime()


def clear_agent_status(agent_id: str) -> bool:
    """清除单个Agent的运行时状态"""
    runtime = _load_runtime()
    if agent_id in runtime:
        del runtime[agent_id]
        _save_runtime(runtime)
        return True
    return False


def clear_all_statuses() -> None:
    """清除所有运行时状态"""
    _save_runtime({})


def has_runtime_data() -> bool:
    """检查是否有运行时数据"""
    return bool(_load_runtime())
