"""MiMo Code 状态监控器。"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from typing import Any

from app.core.constants import AgentStatus
from app.core.state_manager import state_manager


# Agent IDs
AGENT_ID_POWERSHELL = "mimo_code_powershell"
AGENT_ID_VSCODE = "mimo_code_vscode"

# Agent 元数据
AGENT_NAME = "MiMo Code"
CHANNEL_POWERSHELL = "PowerShell"
CHANNEL_VSCODE = "VS Code"

# 进程名模式
PROCESS_PATTERNS_POWERSHELL = ["mimo.exe", "MiMo.exe"]
PROCESS_PATTERNS_VSCODE = ["mimo.exe", "MiMo.exe"]


class MiMoMonitor:
    """MiMo Code 状态监控器"""

    def __init__(self):
        self._powershell_running = False
        self._vscode_running = False
        self._powershell_started_at: str | None = None
        self._vscode_started_at: str | None = None
        self._powershell_last_activity: str | None = None
        self._vscode_last_activity: str | None = None

    def _check_process_by_pattern(self, patterns: list[str]) -> bool:
        """检测指定进程模式"""
        try:
            if sys.platform != "win32":
                return False

            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            output = result.stdout.lower()
            for pattern in patterns:
                if pattern.lower() in output:
                    return True

            return False

        except Exception:
            return False

    def check_processes(self) -> dict[str, bool]:
        """
        检测 MiMo Code 各实例状态。

        Returns:
            dict: 各实例运行状态
        """
        # 检测 PowerShell 实例
        powershell_running = self._check_process_by_pattern(PROCESS_PATTERNS_POWERSHELL)

        # 检测 VS Code 实例（目前使用相同进程名，实际可能需要区分）
        vscode_running = powershell_running  # 简化处理

        self._powershell_running = powershell_running
        self._vscode_running = vscode_running

        # 更新最后活动时间
        if powershell_running:
            self._powershell_last_activity = datetime.now().isoformat()
        if vscode_running:
            self._vscode_last_activity = datetime.now().isoformat()

        return {
            "powershell": powershell_running,
            "vscode": vscode_running,
        }

    def _get_running_time(self, started_at: str | None) -> str:
        """获取运行时间"""
        if not started_at:
            return "未运行"

        try:
            start = datetime.fromisoformat(started_at)
            now = datetime.now()
            elapsed = (now - start).total_seconds()

            if elapsed < 60:
                return f"{int(elapsed)}秒"
            elif elapsed < 3600:
                return f"{int(elapsed // 60)}分钟"
            else:
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                return f"{hours}小时{minutes}分钟"
        except Exception:
            return "未知"

    def _update_agent_state(
        self,
        agent_id: str,
        channel: str,
        is_running: bool,
        started_at: str | None,
        last_activity: str | None,
    ) -> dict[str, Any]:
        """更新单个 Agent 状态"""
        state = state_manager.get_state()
        agent = state.agents.get(agent_id)

        if is_running:
            status = AgentStatus.RUNNING
            health = "GOOD"
            message = f"MiMo Code ({channel}) 运行中"

            # 记录首次启动时间
            if not started_at:
                started_at = datetime.now().isoformat()
        else:
            status = AgentStatus.IDLE
            health = "GOOD"
            message = f"MiMo Code ({channel}) 未运行"
            started_at = None
            last_activity = None

        if agent:
            agent.status = status
            agent.health = health
            agent.message = message
            agent.started_at = started_at or ""
            agent.last_activity = last_activity or ""
            agent.updated = datetime.now().isoformat()
        else:
            from app.core.models import AgentState
            agent = AgentState(
                id=agent_id,
                name=AGENT_NAME,
                channel=channel,
                status=status,
                health=health,
                message=message,
                started_at=started_at or "",
                last_activity=last_activity or "",
                updated=datetime.now().isoformat(),
            )
            state.agents[agent_id] = agent

        state_manager.save()

        return {
            "process": "Running" if is_running else "Not Running",
            "status": status,
            "health": health,
            "message": message,
            "started_at": started_at or "未运行",
            "last_activity": last_activity or "无",
            "running_time": self._get_running_time(started_at),
        }

    def update_state(self) -> dict[str, Any]:
        """
        更新 MiMo Code 状态到 workstation_state.json。

        Returns:
            更新后的状态信息
        """
        try:
            # 检测进程
            processes = self.check_processes()

            # 更新 PowerShell 实例
            powershell_result = self._update_agent_state(
                agent_id=AGENT_ID_POWERSHELL,
                channel=CHANNEL_POWERSHELL,
                is_running=processes["powershell"],
                started_at=self._powershell_started_at,
                last_activity=self._powershell_last_activity,
            )

            # 更新 VS Code 实例
            vscode_result = self._update_agent_state(
                agent_id=AGENT_ID_VSCODE,
                channel=CHANNEL_VSCODE,
                is_running=processes["vscode"],
                started_at=self._vscode_started_at,
                last_activity=self._vscode_last_activity,
            )

            return {
                "powershell": powershell_result,
                "vscode": vscode_result,
                "updated": True,
            }

        except Exception as e:
            # 异常情况
            state_manager.update_agent(
                agent_id=AGENT_ID_POWERSHELL,
                status=AgentStatus.ERROR,
                message=f"检测异常: {str(e)[:100]}",
                name=AGENT_NAME,
                channel=CHANNEL_POWERSHELL,
            )
            state_manager.update_agent(
                agent_id=AGENT_ID_VSCODE,
                status=AgentStatus.ERROR,
                message=f"检测异常: {str(e)[:100]}",
                name=AGENT_NAME,
                channel=CHANNEL_VSCODE,
            )

            return {
                "powershell": {"process": "Error", "status": AgentStatus.ERROR},
                "vscode": {"process": "Error", "status": AgentStatus.ERROR},
                "updated": True,
                "error": str(e)[:100],
            }


# 全局监控器实例
mimo_monitor = MiMoMonitor()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== MiMo Monitor ===")
    print()

    monitor = MiMoMonitor()
    result = monitor.update_state()

    print(f"PowerShell: {result['powershell']['process']}")
    print(f"VS Code: {result['vscode']['process']}")
    print()
    print(f"PowerShell Status: {result['powershell']['status']}")
    print(f"VS Code Status: {result['vscode']['status']}")


if __name__ == "__main__":
    main()
