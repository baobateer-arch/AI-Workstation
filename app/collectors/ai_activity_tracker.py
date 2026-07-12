"""AI 活跃追踪器 - 使用 Event Log 统计 AI Agent 活跃情况。"""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path
from typing import Any

from app.core.state_manager import state_manager


# 数据目录
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
EVENTS_FILE = DATA_DIR / "events.jsonl"


class AIActivityTracker:
    """AI 活跃追踪器"""

    def __init__(self):
        self._sessions_today = 0
        self._tool_calls_today = 0
        self._active_minutes = 0
        self._last_active: str | None = None

    def _load_events(self) -> list[dict[str, Any]]:
        """加载 events.jsonl"""
        if not EVENTS_FILE.exists():
            return []

        entries = []
        try:
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

        return entries

    def _is_today(self, timestamp: str | None) -> bool:
        """检查时间戳是否是今天"""
        if not timestamp:
            return False

        try:
            # 尝试解析 ISO 格式
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.date() == date.today()
        except Exception:
            pass

        try:
            # 尝试解析其他格式
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                try:
                    dt = datetime.strptime(timestamp[:19], fmt)
                    return dt.date() == date.today()
                except ValueError:
                    continue
        except Exception:
            pass

        return False

    def _count_sessions(self, events: list[dict[str, Any]]) -> int:
        """统计今日会话数（event_type=session_start）"""
        count = 0
        for entry in events:
            timestamp = entry.get("timestamp", "")
            event_type = entry.get("event_type", "")

            if self._is_today(timestamp) and event_type == "session_start":
                count += 1
        return count

    def _count_tool_calls(self, events: list[dict[str, Any]]) -> int:
        """统计今日工具调用数（event_type=tool_use）"""
        count = 0
        for entry in events:
            timestamp = entry.get("timestamp", "")
            event_type = entry.get("event_type", "")

            if self._is_today(timestamp) and event_type == "tool_use":
                count += 1
        return count

    def _calculate_active_minutes(self, events: list[dict[str, Any]]) -> int:
        """计算今日活跃分钟数"""
        today_timestamps = []

        for entry in events:
            timestamp = entry.get("timestamp", "")
            if self._is_today(timestamp):
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    today_timestamps.append(dt)
                except Exception:
                    continue

        if not today_timestamps:
            return 0

        # 排序
        today_timestamps.sort()

        # 计算第一条和最后一条的时间差
        first = today_timestamps[0]
        last = today_timestamps[-1]
        total_minutes = int((last - first).total_seconds() / 60)

        return max(total_minutes, 1)

    def _find_last_active(self, events: list[dict[str, Any]]) -> str | None:
        """查找最后活跃时间"""
        latest = None

        for entry in events:
            timestamp = entry.get("timestamp", "")
            if self._is_today(timestamp) and timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if latest is None or dt > latest:
                        latest = dt
                except Exception:
                    continue

        return latest.isoformat() if latest else None

    def track(self) -> dict[str, Any]:
        """
        追踪 AI 活跃情况。

        Returns:
            追踪结果
        """
        # 加载事件日志
        events = self._load_events()

        # 统计
        self._sessions_today = self._count_sessions(events)
        self._tool_calls_today = self._count_tool_calls(events)
        self._active_minutes = self._calculate_active_minutes(events)
        self._last_active = self._find_last_active(events)

        return {
            "sessions_today": self._sessions_today,
            "tool_calls_today": self._tool_calls_today,
            "active_minutes": self._active_minutes,
            "last_active": self._last_active,
        }

    def update_state(self) -> dict[str, Any]:
        """
        更新 AI 活跃状态到 workstation_state.json。

        Returns:
            更新后的状态信息
        """
        try:
            activity = self.track()

            # 更新资源状态
            state = state_manager.get_state()
            state.resource.updated = datetime.now().isoformat()
            state_manager.save()

            return {
                "name": "AI Activity",
                "sessions_today": activity["sessions_today"],
                "tool_calls_today": activity["tool_calls_today"],
                "active_minutes": activity["active_minutes"],
                "last_active": activity["last_active"],
                "updated": True,
            }

        except Exception as e:
            return {
                "name": "AI Activity",
                "sessions_today": 0,
                "tool_calls_today": 0,
                "active_minutes": 0,
                "last_active": None,
                "status": "ERROR",
                "error": str(e)[:100],
                "updated": False,
            }


# 全局追踪器实例
ai_activity_tracker = AIActivityTracker()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== AI Activity ===")
    print()

    tracker = AIActivityTracker()
    result = tracker.update_state()

    print(f"Sessions: {result['sessions_today']}")
    print(f"Tool Calls: {result['tool_calls_today']}")
    print(f"Active: {result['active_minutes']} min")
    print(f"State Updated: {'YES' if result['updated'] else 'NO'}")


if __name__ == "__main__":
    main()
