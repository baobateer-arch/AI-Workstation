"""统一状态数据模型，为首页提供决策数据。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass
class DailyGoal:
    """今日目标"""
    completed: int = 0
    target: int = 5
    expected_income: float = 0.0
    avg_minutes: int = 0


@dataclass
class CurrentProject:
    """当前项目"""
    name: str = ""
    elapsed_minutes: int = 0
    target_minutes: int = 60
    ai_cost: float = 0.0
    status: str = "空闲"


@dataclass
class AIResource:
    """AI 资源"""
    codex_percent: float = 0.0
    codex_reset: str = ""
    deepseek_balance: float = 0.0
    deepseek_status: str = "正常"
    mimo_balance: float = 0.0
    mimo_status: str = "正常"


@dataclass
class AgentSummary:
    """Agent 状态汇总"""
    running: int = 0
    needs_attention: int = 0


@dataclass
class WorkState:
    """工作状态汇总"""
    generated_at: str = ""
    daily_goal: DailyGoal = field(default_factory=DailyGoal)
    current_project: CurrentProject = field(default_factory=CurrentProject)
    ai_resource: AIResource = field(default_factory=AIResource)
    agent_summary: AgentSummary = field(default_factory=AgentSummary)
    today_income: float = 0.0
    suggestions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "WorkState":
        goal = d.get("daily_goal", {})
        project = d.get("current_project", {})
        resource = d.get("ai_resource", {})
        agent = d.get("agent_summary", {})

        return cls(
            generated_at=str(d.get("generated_at", "")),
            daily_goal=DailyGoal(
                completed=int(goal.get("completed", 0)),
                target=int(goal.get("target", 5)),
                expected_income=float(goal.get("expected_income", 0)),
                avg_minutes=int(goal.get("avg_minutes", 0)),
            ),
            current_project=CurrentProject(
                name=str(project.get("name", "")),
                elapsed_minutes=int(project.get("elapsed_minutes", 0)),
                target_minutes=int(project.get("target_minutes", 60)),
                ai_cost=float(project.get("ai_cost", 0)),
                status=str(project.get("status", "空闲")),
            ),
            ai_resource=AIResource(
                codex_percent=float(resource.get("codex_percent", 0)),
                codex_reset=str(resource.get("codex_reset", "")),
                deepseek_balance=float(resource.get("deepseek_balance", 0)),
                deepseek_status=str(resource.get("deepseek_status", "正常")),
                mimo_balance=float(resource.get("mimo_balance", 0)),
                mimo_status=str(resource.get("mimo_status", "正常")),
            ),
            agent_summary=AgentSummary(
                running=int(agent.get("running", 0)),
                needs_attention=int(agent.get("needs_attention", 0)),
            ),
            today_income=float(d.get("today_income", 0)),
            suggestions=list(d.get("suggestions", [])),
        )


def build_work_state(
    goal_data: dict[str, Any] | None = None,
    project_data: dict[str, Any] | None = None,
    resource_data: dict[str, Any] | None = None,
    agent_data: dict[str, Any] | None = None,
    income: float = 0.0,
) -> WorkState:
    """从各模块数据构建工作状态。"""
    suggestions = []
    state = WorkState(
        generated_at=datetime.now().isoformat(),
        today_income=income,
    )

    if goal_data:
        state.daily_goal = DailyGoal(
            completed=int(goal_data.get("completed", 0)),
            target=int(goal_data.get("target", 5)),
            expected_income=float(goal_data.get("expected_income", 0)),
            avg_minutes=int(goal_data.get("avg_minutes", 0)),
        )

    if project_data:
        state.current_project = CurrentProject(
            name=str(project_data.get("name", "")),
            elapsed_minutes=int(project_data.get("elapsed_minutes", 0)),
            target_minutes=int(project_data.get("target_minutes", 60)),
            ai_cost=float(project_data.get("ai_cost", 0)),
            status=str(project_data.get("status", "空闲")),
        )

    if resource_data:
        state.ai_resource = AIResource(
            codex_percent=float(resource_data.get("codex_percent", 0)),
            codex_reset=str(resource_data.get("codex_reset", "")),
            deepseek_balance=float(resource_data.get("deepseek_balance", 0)),
            deepseek_status=str(resource_data.get("deepseek_status", "正常")),
            mimo_balance=float(resource_data.get("mimo_balance", 0)),
            mimo_status=str(resource_data.get("mimo_status", "正常")),
        )

    if agent_data:
        state.agent_summary = AgentSummary(
            running=int(agent_data.get("running", 0)),
            needs_attention=int(agent_data.get("needs_attention", 0)),
        )

    state.suggestions = suggestions
    return state
