"""Agent 聚合层 - 将多个 Agent 实例聚合成展示层 Agent。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.constants import AgentStatus
from app.core.state_manager import state_manager


# 聚合规则：展示层 Agent -> 实例列表
AGENT_AGGREGATION = {
    "claude": ["claude_code_vscode"],
    "codex": ["codex_desktop"],
    "mimo": ["mimo_code_powershell", "mimo_code_vscode"],
}

# 状态优先级（数值越小越优先）
STATUS_PRIORITY = {
    AgentStatus.ERROR: 0,
    AgentStatus.PERMISSION: 1,
    AgentStatus.WAITING: 2,
    AgentStatus.RUNNING: 3,
    AgentStatus.DONE: 4,
    AgentStatus.IDLE: 5,
    AgentStatus.STOPPED: 6,
}


@dataclass
class AggregatedAgent:
    """聚合后的 Agent"""
    id: str
    name: str
    status: str = AgentStatus.IDLE
    health: str = "GOOD"
    message: str = ""
    instances: list[dict[str, Any]] = field(default_factory=list)
    channels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "health": self.health,
            "message": self.message,
            "instances": self.instances,
            "channels": self.channels,
        }


def _get_priority(status: str) -> int:
    """获取状态优先级"""
    return STATUS_PRIORITY.get(status, 99)


def _select_highest_priority(statuses: list[str]) -> str:
    """选择最高优先级状态"""
    if not statuses:
        return AgentStatus.IDLE

    return min(statuses, key=_get_priority)


def _select_health(healths: list[str]) -> str:
    """选择健康状态（任一 ERROR 则 ERROR）"""
    if "ERROR" in healths:
        return "ERROR"
    if "WARNING" in healths:
        return "WARNING"
    return "GOOD"


def _build_message(status: str, names: list[str]) -> str:
    """构建消息"""
    if status == AgentStatus.ERROR:
        return f"{', '.join(names)} 存在异常"
    elif status == AgentStatus.PERMISSION:
        return f"{', '.join(names)} 等待授权"
    elif status == AgentStatus.WAITING:
        return f"{', '.join(names)} 等待输入"
    elif status == AgentStatus.RUNNING:
        return f"{', '.join(names)} 运行中"
    elif status == AgentStatus.DONE:
        return f"{', '.join(names)} 已完成"
    else:
        return f"{', '.join(names)} 空闲"


def aggregate_agents() -> dict[str, AggregatedAgent]:
    """
    聚合所有 Agent 实例。

    Returns:
        dict: 聚合后的 Agent 字典
    """
    state = state_manager.get_state()
    aggregated = {}

    for agent_id, instance_ids in AGENT_AGGREGATION.items():
        # 收集该聚合组下所有实例
        instances = []
        statuses = []
        healths = []
        channels = []
        instance_names = []

        for instance_id in instance_ids:
            agent = state.agents.get(instance_id)
            if agent:
                instances.append({
                    "id": agent.id,
                    "status": agent.status,
                    "health": agent.health,
                    "message": agent.message,
                    "started_at": agent.started_at,
                    "last_activity": agent.last_activity,
                })
                statuses.append(agent.status)
                healths.append(agent.health)
                channels.append(agent.channel)
                instance_names.append(agent.channel)

        # 聚合状态
        status = _select_highest_priority(statuses) if statuses else AgentStatus.IDLE
        health = _select_health(healths) if healths else "GOOD"
        message = _build_message(status, instance_names) if instance_names else "无实例"

        # 创建聚合 Agent
        aggregated[agent_id] = AggregatedAgent(
            id=agent_id,
            name=agent_id.upper(),
            status=status,
            health=health,
            message=message,
            instances=instances,
            channels=channels,
        )

    return aggregated


def get_aggregated_list() -> list[dict[str, Any]]:
    """
    获取聚合后的 Agent 列表。

    Returns:
        list: 聚合 Agent 字典列表
    """
    aggregated = aggregate_agents()
    return [agent.to_dict() for agent in aggregated.values()]


def get_attention_agents() -> list[dict[str, Any]]:
    """
    获取需要关注的聚合 Agent。

    Returns:
        list: 需要关注的 Agent 列表
    """
    aggregated = aggregate_agents()
    attention = []

    for agent in aggregated.values():
        if AgentStatus.needs_attention(agent.status):
            attention.append(agent.to_dict())

    return attention


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Agent Aggregator ===")
    print()

    aggregated = aggregate_agents()

    for agent_id, agent in aggregated.items():
        print(f"{agent.name}:")
        print(f"  Status: {agent.status}")
        print(f"  Health: {agent.health}")
        print(f"  Message: {agent.message}")
        print(f"  Channels: {agent.channels}")
        print(f"  Instances: {len(agent.instances)}")
        print()


if __name__ == "__main__":
    main()
