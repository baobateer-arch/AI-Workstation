"""数据模型定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.constants import AgentStatus


@dataclass
class AgentState:
    """Agent 状态"""
    id: str
    name: str
    channel: str
    status: str = AgentStatus.IDLE
    health: str = "GOOD"
    message: str = ""
    project: str = ""
    started_at: str = ""
    last_activity: str = ""
    updated: str = ""

    def __post_init__(self):
        # 标准化状态为大写
        self.status = AgentStatus.normalize(self.status)

    @property
    def needs_attention(self) -> bool:
        return AgentStatus.needs_attention(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "channel": self.channel,
            "status": self.status,
            "health": self.health,
            "message": self.message,
            "project": self.project,
            "started_at": self.started_at,
            "last_activity": self.last_activity,
            "updated": self.updated or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            channel=data.get("channel", ""),
            status=AgentStatus.normalize(data.get("status", AgentStatus.IDLE)),
            health=data.get("health", "GOOD"),
            message=data.get("message", ""),
            project=data.get("project", ""),
            started_at=data.get("started_at", ""),
            last_activity=data.get("last_activity", ""),
            updated=data.get("updated", ""),
        )


@dataclass
class ResourceState:
    """AI 资源状态"""
    # Codex 5小时额度
    codex_percent: float = 100.0
    codex_reset_at: str = ""
    # Codex 每周额度
    codex_weekly_percent: float = 100.0
    codex_weekly_reset_at: str = ""
    # 其他资源
    deepseek_balance: float = 0.0
    mimo_balance: float = 0.0
    updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "codex_percent": self.codex_percent,
            "codex_reset_at": self.codex_reset_at,
            "codex_weekly_percent": self.codex_weekly_percent,
            "codex_weekly_reset_at": self.codex_weekly_reset_at,
            "deepseek_balance": self.deepseek_balance,
            "mimo_balance": self.mimo_balance,
            "updated": self.updated or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceState":
        return cls(
            codex_percent=float(data.get("codex_percent", 100)),
            codex_reset_at=data.get("codex_reset_at", ""),
            codex_weekly_percent=float(data.get("codex_weekly_percent", 100)),
            codex_weekly_reset_at=data.get("codex_weekly_reset_at", ""),
            deepseek_balance=float(data.get("deepseek_balance", 0)),
            mimo_balance=float(data.get("mimo_balance", 0)),
            updated=data.get("updated", ""),
        )


@dataclass
class ProjectState:
    """项目状态"""
    name: str = ""
    elapsed_minutes: int = 0
    target_minutes: int = 60
    ai_cost: float = 0.0
    status: str = ""
    updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "elapsed_minutes": self.elapsed_minutes,
            "target_minutes": self.target_minutes,
            "ai_cost": self.ai_cost,
            "status": self.status,
            "updated": self.updated or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectState":
        return cls(
            name=data.get("name", ""),
            elapsed_minutes=int(data.get("elapsed_minutes", 0)),
            target_minutes=int(data.get("target_minutes", 60)),
            ai_cost=float(data.get("ai_cost", 0)),
            status=data.get("status", ""),
            updated=data.get("updated", ""),
        )


@dataclass
class CCModelState:
    """Claude Code 模型状态"""
    provider: str = ""
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CCModelState":
        return cls(
            provider=data.get("provider", ""),
            model=data.get("model", ""),
        )


@dataclass
class WorkstationState:
    """工作站完整状态"""
    agents: dict[str, AgentState] = field(default_factory=dict)
    resource: ResourceState = field(default_factory=ResourceState)
    project: ProjectState = field(default_factory=ProjectState)
    cc_model: CCModelState = field(default_factory=CCModelState)
    updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "resource": self.resource.to_dict(),
            "project": self.project.to_dict(),
            "cc_model": self.cc_model.to_dict(),
            "updated": self.updated or datetime.now().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkstationState":
        agents = {}
        for agent_id, agent_data in data.get("agents", {}).items():
            agents[agent_id] = AgentState.from_dict({**agent_data, "id": agent_id})

        return cls(
            agents=agents,
            resource=ResourceState.from_dict(data.get("resource", {})),
            project=ProjectState.from_dict(data.get("project", {})),
            cc_model=CCModelState.from_dict(data.get("cc_model", {})),
            updated=data.get("updated", ""),
        )
