"""Agent status data models and helper functions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


# ---------------------------------------------------------------------------
# 状态常量
# ---------------------------------------------------------------------------

STATUS_IDLE = "idle"
STATUS_RUNNING = "running"
STATUS_PERMISSION = "permission_required"
STATUS_INPUT = "input_required"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"

STATUS_CN = {
    STATUS_IDLE: "空闲",
    STATUS_RUNNING: "运行中",
    STATUS_PERMISSION: "需要授权",
    STATUS_INPUT: "等待回复",
    STATUS_COMPLETED: "任务完成",
    STATUS_ERROR: "运行异常",
}

# 固定优先级：数值越小越优先
PRIORITY = {
    STATUS_PERMISSION: 0,
    STATUS_INPUT: 1,
    STATUS_ERROR: 2,
    STATUS_COMPLETED: 3,
    STATUS_RUNNING: 4,
    STATUS_IDLE: 5,
}

# 需要处理的状态（除 running 和 idle 外）
NEEDS_ATTENTION_STATUSES = {STATUS_PERMISSION, STATUS_INPUT, STATUS_ERROR, STATUS_COMPLETED}


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class AgentInfo:
    id: str
    name: str
    status: str
    project: str
    task: str
    message: str
    started_at: str | None = None
    waiting_since: str | None = None
    needs_attention: bool = False

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "AgentInfo":
        return cls(
            id=str(d.get("id", "")),
            name=str(d.get("name", "")),
            status=str(d.get("status", STATUS_IDLE)),
            project=str(d.get("project", "")),
            task=str(d.get("task", "")),
            message=str(d.get("message", "")),
            started_at=d.get("started_at"),
            waiting_since=d.get("waiting_since"),
            needs_attention=bool(d.get("needs_attention", False)),
        )


@dataclass
class AgentDashboardData:
    generated_at: str
    agents: list[AgentInfo]

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "AgentDashboardData":
        agents = [AgentInfo.from_dict(a) for a in d.get("agents", [])]
        return cls(
            generated_at=str(d.get("generated_at", "")),
            agents=agents,
        )


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _to_naive(dt: datetime) -> datetime:
    """将 aware datetime 转为 naive（去掉时区信息）。"""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def minutes_between(start: str | None, end: datetime | None) -> int | None:
    """计算两个时间之间的分钟数。"""
    dt = _parse_dt(start)
    if dt is None or end is None:
        return None
    return max(0, int((_to_naive(end) - _to_naive(dt)).total_seconds() // 60))


def status_cn(status: str) -> str:
    return STATUS_CN.get(status, status)


def priority_of(status: str) -> int:
    return PRIORITY.get(status, 99)
