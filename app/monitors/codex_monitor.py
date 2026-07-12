"""Codex Desktop 状态监控器。"""

from __future__ import annotations

import os
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.constants import AgentStatus
from app.core.state_manager import state_manager


# Agent ID
AGENT_ID = "codex_desktop"

# Agent 元数据
AGENT_NAME = "Codex"
AGENT_CHANNEL = "桌面端"

# 进程名模式
PROCESS_PATTERNS = ["codex.exe", "Codex.exe"]

# 活跃超时（30分钟）
ACTIVITY_TIMEOUT_MINUTES = 30

# 需要忽略的目录名（精确匹配）
IGNORED_DIR_NAMES = {
    "node_modules",
    "python",
    "lib",
    "scripts",
    "site-packages",
    "__pycache__",
    ".venv",
    "venv",
}

# 需要忽略的系统路径前缀
IGNORED_PATH_PREFIXES = [
    "c:\\windows",
    "c:\\program files\\python",
    "c:\\program files\\nodejs",
    "c:\\program files\\windowsapps",
]

# 未知项目标识
UNKNOWN_PROJECT = "未知项目"


def _is_ignored_path(path: str) -> bool:
    """检查路径是否应该被忽略"""
    path_lower = path.lower().replace("/", "\\")
    dir_name = path.split("\\")[-1].lower() if "\\" in path else path.lower()

    # 检查目录名
    if dir_name in IGNORED_DIR_NAMES:
        return True

    # 检查路径前缀
    for prefix in IGNORED_PATH_PREFIXES:
        if path_lower.startswith(prefix):
            return True

    return False


def _find_git_root(start_path: str) -> str | None:
    """向上查找 .git 目录，返回项目根目录"""
    current = Path(start_path)

    # 最多向上查找 10 层
    for _ in range(10):
        if current == current.parent:
            break

        git_dir = current / ".git"
        if git_dir.exists():
            return str(current)

        current = current.parent

    return None


def _extract_project_name(path: str) -> str:
    """从路径提取项目名称"""
    if not path:
        return UNKNOWN_PROJECT

    # 清理路径
    path = path.strip().strip('"').strip("'")

    # 如果是文件路径，取父目录
    if os.path.isfile(path):
        path = os.path.dirname(path)

    # 忽略系统路径
    if _is_ignored_path(path):
        return UNKNOWN_PROJECT

    # 尝试查找 git 根目录
    git_root = _find_git_root(path)
    if git_root:
        project = Path(git_root).name
        if project and not _is_ignored_path(project):
            return project

    # 提取最后一级目录名
    project = Path(path).name
    if project and not _is_ignored_path(project) and len(project) < 50:
        return project

    return UNKNOWN_PROJECT


class CodexMonitor:
    """Codex Desktop 状态监控器"""

    def __init__(self):
        self._running = False
        self._started_at: str | None = None
        self._last_activity: str | None = None
        self._project: str = UNKNOWN_PROJECT

    def check_process(self) -> bool:
        """
        检测 Windows 是否存在 Codex 进程。

        Returns:
            True 如果进程运行中
        """
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
            for pattern in PROCESS_PATTERNS:
                if pattern.lower() in output:
                    self._running = True
                    self._last_activity = datetime.now().isoformat()
                    return True

            self._running = False
            return False

        except Exception:
            self._running = False
            return False

    def _detect_project(self) -> str:
        """
        检测当前项目。

        优先级：
        1. Codex 当前工作目录
        2. 向上查找 .git
        3. workspace 信息
        """
        if sys.platform != "win32":
            return UNKNOWN_PROJECT

        try:
            # 使用 wmic 获取进程详情（使用 LIST 格式避免逗号问题）
            result = subprocess.run(
                ["wmic", "process", "where", "name='codex.exe'",
                 "get", "ExecutablePath", "/FORMAT:LIST"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            output = result.stdout
            for line in output.split("\n"):
                if "ExecutablePath=" in line:
                    path = line.split("ExecutablePath=")[1].strip()
                    if path and path != "ExecutablePath":
                        project = _extract_project_name(path)
                        if project != UNKNOWN_PROJECT:
                            return project

        except Exception:
            pass

        return UNKNOWN_PROJECT

    def _get_running_time(self) -> str:
        """获取运行时间"""
        if not self._started_at:
            return "未运行"

        try:
            start = datetime.fromisoformat(self._started_at)
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

    def _is_activity_timeout(self) -> bool:
        """检查是否超过活跃超时"""
        if not self._last_activity:
            return True

        try:
            last = datetime.fromisoformat(self._last_activity)
            now = datetime.now()
            elapsed_minutes = (now - last).total_seconds() / 60
            return elapsed_minutes > ACTIVITY_TIMEOUT_MINUTES
        except Exception:
            return True

    def update_state(self) -> dict[str, Any]:
        """
        更新 Codex Desktop 状态到 workstation_state.json。

        Returns:
            更新后的状态信息
        """
        try:
            is_running = self.check_process()

            # 记录首次启动时间
            if is_running and not self._started_at:
                self._started_at = datetime.now().isoformat()
            elif not is_running:
                self._started_at = None
                self._last_activity = None

            # 检测项目
            if is_running:
                project = self._detect_project()
                self._project = project

            # 判断状态
            if is_running:
                if self._is_activity_timeout():
                    status = AgentStatus.IDLE
                    health = "WARNING"
                    message = "Codex 运行但无活动"
                else:
                    status = AgentStatus.RUNNING
                    health = "GOOD"
                    message = "Codex Desktop 运行中"
            else:
                status = AgentStatus.IDLE
                health = "GOOD"
                message = "Codex Desktop 未运行"

            # 更新状态
            state = state_manager.get_state()
            agent = state.agents.get(AGENT_ID)

            if agent:
                agent.status = status
                agent.message = message
                agent.project = self._project
                if is_running and self._started_at:
                    agent.started_at = self._started_at
                if self._last_activity:
                    agent.last_activity = self._last_activity
                agent.updated = datetime.now().isoformat()
            else:
                from app.core.models import AgentState
                agent = AgentState(
                    id=AGENT_ID,
                    name=AGENT_NAME,
                    channel=AGENT_CHANNEL,
                    status=status,
                    message=message,
                    project=self._project,
                    started_at=self._started_at or "",
                    last_activity=self._last_activity or "",
                    updated=datetime.now().isoformat(),
                )
                state.agents[AGENT_ID] = agent

            state_manager.save()

            return {
                "process": "Running" if is_running else "Not Running",
                "status": status,
                "health": health,
                "message": message,
                "project": self._project,
                "started_at": self._started_at or "未运行",
                "last_activity": self._last_activity or "无",
                "running_time": self._get_running_time(),
                "updated": True,
            }

        except Exception as e:
            # 异常情况
            state_manager.update_agent(
                agent_id=AGENT_ID,
                status=AgentStatus.ERROR,
                message=f"检测异常: {str(e)[:100]}",
                name=AGENT_NAME,
                channel=AGENT_CHANNEL,
            )

            return {
                "process": "Error",
                "status": AgentStatus.ERROR,
                "health": "ERROR",
                "message": str(e)[:100],
                "project": UNKNOWN_PROJECT,
                "started_at": "未知",
                "last_activity": "未知",
                "running_time": "未知",
                "updated": True,
            }

    @property
    def is_running(self) -> bool:
        return self._running


# 全局监控器实例
codex_monitor = CodexMonitor()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Codex Monitor ===")
    print()

    monitor = CodexMonitor()
    result = monitor.update_state()

    print(f"Process: {result['process']}")
    print(f"Project: {result['project']}")
    print(f"Status: {result['status']}")
    print(f"Health: {result['health']}")
    print(f"Running Time: {result['running_time']}")
    print(f"Last Activity: {result['last_activity']}")
    print(f"State Updated: {'YES' if result['updated'] else 'NO'}")


if __name__ == "__main__":
    main()
