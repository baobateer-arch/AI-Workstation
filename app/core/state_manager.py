"""状态管理器 - 统一管理工作站状态。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.models import (
    AgentState,
    CCModelState,
    ResourceState,
    ProjectState,
    WorkstationState,
)
from app.core.event_bus import (
    event_bus,
    EVENT_AGENT_UPDATED,
    EVENT_RESOURCE_UPDATED,
    EVENT_PROJECT_UPDATED,
    EVENT_STATE_CHANGED,
)


# 数据文件路径
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
STATE_FILE = DATA_DIR / "workstation_state.json"


class StateManager:
    """工作站状态管理器"""

    def __init__(self, state_file: Path | None = None):
        self._state_file = state_file or STATE_FILE
        self._state: WorkstationState | None = None

    def _ensure_data_dir(self) -> None:
        """确保数据目录存在"""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> WorkstationState:
        """加载状态"""
        self._ensure_data_dir()

        if self._state_file.exists():
            try:
                with open(self._state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._state = WorkstationState.from_dict(data)
            except Exception:
                self._state = WorkstationState()
        else:
            self._state = WorkstationState()

        return self._state

    def save(self) -> None:
        """保存状态"""
        if self._state is None:
            return

        self._ensure_data_dir()
        self._state.updated = datetime.now().isoformat()

        with open(self._state_file, "w", encoding="utf-8") as f:
            json.dump(self._state.to_dict(), f, ensure_ascii=False, indent=2)

    def get_state(self) -> WorkstationState:
        """获取当前状态"""
        if self._state is None:
            self.load()
        return self._state

    def update_agent(
        self,
        agent_id: str,
        status: str,
        message: str = "",
        name: str = "",
        channel: str = "",
        project: str = "",
        last_activity: str = "",
    ) -> AgentState:
        """
        更新 Agent 状态。

        Args:
            agent_id: Agent 标识符
            status: 状态
            message: 消息
            name: Agent 名称
            channel: 渠道
            project: 项目
            last_activity: 最后活动时间（相对格式，如 "8 min ago"）

        Returns:
            更新后的 AgentState
        """
        state = self.get_state()

        if agent_id in state.agents:
            agent = state.agents[agent_id]
            agent.status = status
            if message:
                agent.message = message
            if name:
                agent.name = name
            if channel:
                agent.channel = channel
            if project:
                agent.project = project
            if last_activity:
                agent.last_activity = last_activity
            agent.updated = datetime.now().isoformat()
        else:
            agent = AgentState(
                id=agent_id,
                name=name or agent_id,
                channel=channel or "unknown",
                status=status,
                message=message,
                project=project,
                last_activity=last_activity,
                updated=datetime.now().isoformat(),
            )
            state.agents[agent_id] = agent

        self.save()
        event_bus.emit(EVENT_AGENT_UPDATED, agent)
        event_bus.emit(EVENT_STATE_CHANGED, state)

        return agent

    def update_resource(
        self,
        codex_percent: float | None = None,
        deepseek_balance: float | None = None,
        mimo_balance: float | None = None,
    ) -> ResourceState:
        """
        更新 AI 资源状态。

        Returns:
            更新后的 ResourceState
        """
        state = self.get_state()

        if codex_percent is not None:
            state.resource.codex_percent = codex_percent
        if deepseek_balance is not None:
            state.resource.deepseek_balance = deepseek_balance
        if mimo_balance is not None:
            state.resource.mimo_balance = mimo_balance

        state.resource.updated = datetime.now().isoformat()

        self.save()
        event_bus.emit(EVENT_RESOURCE_UPDATED, state.resource)
        event_bus.emit(EVENT_STATE_CHANGED, state)

        return state.resource

    def update_project(
        self,
        name: str | None = None,
        elapsed_minutes: int | None = None,
        target_minutes: int | None = None,
        ai_cost: float | None = None,
        status: str | None = None,
    ) -> ProjectState:
        """
        更新项目状态。

        Returns:
            更新后的 ProjectState
        """
        state = self.get_state()

        if name is not None:
            state.project.name = name
        if elapsed_minutes is not None:
            state.project.elapsed_minutes = elapsed_minutes
        if target_minutes is not None:
            state.project.target_minutes = target_minutes
        if ai_cost is not None:
            state.project.ai_cost = ai_cost
        if status is not None:
            state.project.status = status

        state.project.updated = datetime.now().isoformat()

        self.save()
        event_bus.emit(EVENT_PROJECT_UPDATED, state.project)
        event_bus.emit(EVENT_STATE_CHANGED, state)

        return state.project

    def update_cc_model(
        self,
        provider: str = "",
        model: str = "",
    ) -> CCModelState:
        """
        更新 Claude Code 模型状态。

        Returns:
            更新后的 CCModelState
        """
        state = self.get_state()

        if provider:
            state.cc_model.provider = provider
        if model:
            state.cc_model.model = model

        self.save()
        event_bus.emit(EVENT_STATE_CHANGED, state)

        return state.cc_model

    def get_attention_agents(self) -> list[AgentState]:
        """获取需要关注的 Agent"""
        state = self.get_state()
        return [a for a in state.agents.values() if a.needs_attention]

    def get_summary(self) -> dict[str, Any]:
        """获取状态摘要"""
        state = self.get_state()
        attention = self.get_attention_agents()

        return {
            "total_agents": len(state.agents),
            "running": sum(1 for a in state.agents.values() if a.status == "running"),
            "needs_attention": len(attention),
            "attention_names": [a.name for a in attention],
            "codex_percent": state.resource.codex_percent,
            "deepseek_balance": state.resource.deepseek_balance,
            "mimo_balance": state.resource.mimo_balance,
            "project_name": state.project.name,
            "project_elapsed": state.project.elapsed_minutes,
            "project_target": state.project.target_minutes,
        }


# 全局状态管理器实例
state_manager = StateManager()
