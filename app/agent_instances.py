"""Agent 实例定义 - 6个固定Agent。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentInstance:
    """Agent 实例定义"""
    id: str
    name: str
    platform: str
    display_name: str

    def __str__(self) -> str:
        return f"{self.name} ({self.platform})"


# 固定6个Agent
AGENTS = [
    AgentInstance(
        id="claude_code_vscode",
        name="Claude Code",
        platform="VS Code",
        display_name="Claude Code / VS Code",
    ),
    AgentInstance(
        id="codex_desktop",
        name="Codex",
        platform="桌面端",
        display_name="Codex / 桌面端",
    ),
    AgentInstance(
        id="mimo_code_powershell",
        name="MiMo Code",
        platform="PowerShell",
        display_name="MiMo Code / PowerShell",
    ),
    AgentInstance(
        id="claude_desktop",
        name="Claude",
        platform="桌面端",
        display_name="Claude / 桌面端",
    ),
    AgentInstance(
        id="claude_cli_powershell",
        name="Claude CLI",
        platform="PowerShell",
        display_name="Claude CLI / PowerShell",
    ),
    AgentInstance(
        id="mimo_code_vscode",
        name="MiMo Code",
        platform="VS Code",
        display_name="MiMo Code / VS Code",
    ),
]

# 快速查找
AGENT_MAP = {a.id: a for a in AGENTS}


def get_agent(agent_id: str) -> AgentInstance | None:
    return AGENT_MAP.get(agent_id)


def get_all_agent_ids() -> list[str]:
    return [a.id for a in AGENTS]
