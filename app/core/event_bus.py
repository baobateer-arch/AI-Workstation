"""事件总线 - 解耦模块间通信，支持持久化。"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


# 数据目录
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
EVENTS_FILE = DATA_DIR / "events.jsonl"

# 敏感字段（禁止保存）
SENSITIVE_FIELDS = {
    "prompt", "content", "tool_input", "message", "text",
    "api_key", "apikey", "token", "secret", "authorization",
}


class EventBus:
    """事件总线，支持内存分发和持久化"""

    def __init__(self, persist: bool = True):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._persist = persist
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        """确保数据目录存在"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def on(self, event: str, handler: Callable) -> None:
        """注册事件处理器"""
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Callable) -> None:
        """移除事件处理器"""
        if handler in self._handlers[event]:
            self._handlers[event].remove(handler)

    def emit(self, event: str, data: Any = None) -> None:
        """触发事件并持久化"""
        # 内存分发
        for handler in self._handlers.get(event, []):
            try:
                handler(data)
            except Exception:
                pass

        # 持久化
        if self._persist:
            self._log_event(event, data)

    def _log_event(self, event_type: str, data: Any) -> None:
        """记录事件到 JSONL 文件"""
        try:
            # 提取安全字段
            event_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
            }

            # 从 data 中提取安全字段
            if isinstance(data, dict):
                event_entry["agent"] = data.get("agent", data.get("agent_id", ""))
                event_entry["status"] = data.get("status", "")
                event_entry["hook_event"] = data.get("hook_event", "")
            elif hasattr(data, "to_dict"):
                d = data.to_dict()
                event_entry["agent"] = d.get("id", d.get("name", ""))
                event_entry["status"] = d.get("status", "")

            # 写入文件
            with open(EVENTS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_entry, ensure_ascii=False) + "\n")

        except Exception:
            pass

    def clear(self) -> None:
        """清除所有处理器"""
        self._handlers.clear()


# 全局事件总线实例
event_bus = EventBus()


# 事件名称常量
EVENT_AGENT_UPDATED = "agent:updated"
EVENT_RESOURCE_UPDATED = "resource:updated"
EVENT_PROJECT_UPDATED = "project:updated"
EVENT_STATE_CHANGED = "state:changed"

# AI 事件常量
EVENT_SESSION_START = "session_start"
EVENT_TOOL_USE = "tool_use"
EVENT_PERMISSION = "permission"
EVENT_STOP = "stop"
