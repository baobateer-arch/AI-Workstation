"""Agent 管理器 - 提供查询和汇总功能。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agent_instances import AGENTS, AgentInstance
from app.agent_state import (
    STATUS_IDLE,
    STATUS_RUNNING,
    STATUS_WAITING_INPUT,
    STATUS_WAITING_AUTH,
    STATUS_ERROR,
    STATUS_COMPLETED,
    needs_attention,
    get_priority,
    status_cn,
)
from app.agent_runtime import get_all_runtime_statuses, has_runtime_data


# 状态映射：runtime 状态 -> 内部状态
STATUS_MAP = {
    "RUNNING": STATUS_RUNNING,
    "IDLE": STATUS_IDLE,
    "PERMISSION": STATUS_WAITING_AUTH,
    "INPUT": STATUS_WAITING_INPUT,
    "ERROR": STATUS_ERROR,
    "COMPLETED": STATUS_COMPLETED,
}


@dataclass
class AgentStatus:
    """单个Agent的状态"""
    agent: AgentInstance
    status: str = STATUS_IDLE
    project: str = ""
    task: str = ""
    message: str = ""
    elapsed_minutes: int = 0
    source: str = "sample"  # "runtime" 或 "sample"

    @property
    def needs_attention(self) -> bool:
        return needs_attention(self.status)

    @property
    def status_text(self) -> str:
        return status_cn(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.agent.id,
            "name": self.agent.name,
            "platform": self.agent.platform,
            "status": self.status,
            "status_text": self.status_text,
            "project": self.project,
            "task": self.task,
            "message": self.message,
            "elapsed_minutes": self.elapsed_minutes,
            "needs_attention": self.needs_attention,
            "source": self.source,
        }


@dataclass
class AgentSummary:
    """Agent汇总"""
    total: int = 0
    running: int = 0
    idle: int = 0
    needs_attention: int = 0
    attention_agents: list[str] = field(default_factory=list)
    error_count: int = 0
    runtime_count: int = 0
    sample_count: int = 0


def _merge_statuses(
    sample_statuses: dict[str, dict] | None,
    runtime_statuses: dict[str, dict],
) -> dict[str, dict]:
    """合并状态，runtime 优先"""
    merged = {}

    # 先加载 sample 状态
    if sample_statuses:
        for agent_id, status in sample_statuses.items():
            merged[agent_id] = {**status, "_source": "sample"}

    # runtime 状态覆盖
    for agent_id, status in runtime_statuses.items():
        mapped_status = STATUS_MAP.get(status.get("status", "").upper(), STATUS_IDLE)
        merged[agent_id] = {
            "status": mapped_status,
            "message": status.get("message", ""),
            "project": status.get("project", ""),
            "task": "",
            "elapsed_minutes": 0,
            "_source": "runtime",
        }

    return merged


def get_all_agents(
    sample_statuses: dict[str, dict] | None = None,
) -> list[AgentStatus]:
    """获取所有Agent状态，优先使用runtime"""
    runtime_statuses = get_all_runtime_statuses()
    merged = _merge_statuses(sample_statuses, runtime_statuses)

    result = []
    for agent in AGENTS:
        s = merged.get(agent.id, {})
        result.append(AgentStatus(
            agent=agent,
            status=s.get("status", STATUS_IDLE),
            project=s.get("project", ""),
            task=s.get("task", ""),
            message=s.get("message", ""),
            elapsed_minutes=s.get("elapsed_minutes", 0),
            source=s.get("_source", "sample"),
        ))
    return result


def get_attention_agents(
    sample_statuses: dict[str, dict] | None = None,
) -> list[AgentStatus]:
    """获取需要处理的Agent，按优先级排序"""
    all_agents = get_all_agents(sample_statuses)
    attention = [a for a in all_agents if a.needs_attention]
    attention.sort(key=lambda a: get_priority(a.status))
    return attention


def summary(sample_statuses: dict[str, dict] | None = None) -> AgentSummary:
    """获取Agent汇总"""
    all_agents = get_all_agents(sample_statuses)
    attention = get_attention_agents(sample_statuses)

    running = sum(1 for a in all_agents if a.status == STATUS_RUNNING)
    idle = sum(1 for a in all_agents if a.status == STATUS_IDLE)
    errors = sum(1 for a in all_agents if a.status == STATUS_ERROR)
    runtime_count = sum(1 for a in all_agents if a.source == "runtime")
    sample_count = sum(1 for a in all_agents if a.source == "sample")

    return AgentSummary(
        total=len(all_agents),
        running=running,
        idle=idle,
        needs_attention=len(attention),
        attention_agents=[a.agent.name for a in attention],
        error_count=errors,
        runtime_count=runtime_count,
        sample_count=sample_count,
    )
