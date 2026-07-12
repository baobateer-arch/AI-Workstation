"""Attention logic for agent status board."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.agent_models import (
    AgentDashboardData,
    AgentInfo,
    NEEDS_ATTENTION_STATUSES,
    priority_of,
)


def _needs_processing(agent: AgentInfo) -> bool:
    return agent.status in NEEDS_ATTENTION_STATUSES


def get_attention_agents(data: AgentDashboardData) -> list[AgentInfo]:
    """返回所有需要处理的 Agent，按固定优先级排序。"""
    filtered = [a for a in data.agents if _needs_processing(a)]
    filtered.sort(key=lambda a: priority_of(a.status))
    return filtered


def get_highest_priority_agent(data: AgentDashboardData) -> AgentInfo | None:
    """返回优先级最高的 Agent，无需处理时返回 None。"""
    attention = get_attention_agents(data)
    return attention[0] if attention else None


def get_attention_count(data: AgentDashboardData) -> int:
    """返回需要处理的 Agent 数量。"""
    return len(get_attention_agents(data))


def should_show_attention_page(data: AgentDashboardData) -> bool:
    """只要存在 permission_required、input_required、error 或 completed 状态即返回 True。"""
    return any(a.status in NEEDS_ATTENTION_STATUSES for a in data.agents)
