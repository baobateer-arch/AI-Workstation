"""系统状态监控器。"""

from __future__ import annotations

import platform
import subprocess
import sys
from datetime import datetime
from typing import Any

from app.core.state_manager import state_manager


class SystemMonitor:
    """系统状态监控器"""

    def __init__(self):
        self._cpu_percent: float = 0.0
        self._memory_percent: float = 0.0
        self._memory_used: str = ""
        self._memory_total: str = ""
        self._uptime: str = ""

    def _get_cpu_percent(self) -> float:
        """获取 CPU 使用率"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["wmic", "cpu", "get", "LoadPercentage", "/FORMAT:LIST"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split("\n"):
                    if "LoadPercentage=" in line:
                        return float(line.split("=")[1].strip())
            else:
                result = subprocess.run(
                    ["top", "-bn1"], capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split("\n"):
                    if "Cpu(s)" in line:
                        return float(line.split(":")[1].split("%")[0].strip())
        except Exception:
            pass
        return 0.0

    def _get_memory_info(self) -> tuple[float, str, str]:
        """获取内存信息"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/FORMAT:LIST"],
                    capture_output=True, text=True, timeout=5
                )
                free = total = 0
                for line in result.stdout.split("\n"):
                    if "FreePhysicalMemory=" in line:
                        free = int(line.split("=")[1].strip())
                    elif "TotalVisibleMemorySize=" in line:
                        total = int(line.split("=")[1].strip())

                if total > 0:
                    used = total - free
                    percent = (used / total) * 100
                    return percent, f"{used // 1024}MB", f"{total // 1024}MB"
        except Exception:
            pass
        return 0.0, "0MB", "0MB"

    def _get_uptime(self) -> str:
        """获取系统运行时间"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["wmic", "os", "get", "LastBootUpTime", "/FORMAT:LIST"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split("\n"):
                    if "LastBootUpTime=" in line:
                        boot_time_str = line.split("=")[1].strip()
                        boot_time = datetime.strptime(boot_time_str[:14], "%Y%m%d%H%M%S")
                        uptime = datetime.now() - boot_time
                        hours = int(uptime.total_seconds() // 3600)
                        minutes = int((uptime.total_seconds() % 3600) // 60)
                        return f"{hours}h{minutes}m"
        except Exception:
            pass
        return "未知"

    def update_state(self) -> dict[str, Any]:
        """
        更新系统状态。

        Returns:
            系统状态信息
        """
        try:
            self._cpu_percent = self._get_cpu_percent()
            self._memory_percent, self._memory_used, self._memory_total = self._get_memory_info()
            self._uptime = self._get_uptime()

            return {
                "cpu_percent": self._cpu_percent,
                "memory_percent": self._memory_percent,
                "memory_used": self._memory_used,
                "memory_total": self._memory_total,
                "uptime": self._uptime,
                "updated": True,
            }

        except Exception as e:
            return {
                "cpu_percent": 0.0,
                "memory_percent": 0.0,
                "memory_used": "0MB",
                "memory_total": "0MB",
                "uptime": "未知",
                "error": str(e)[:100],
                "updated": False,
            }


# 全局监控器实例
system_monitor = SystemMonitor()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== System Monitor ===")
    print()

    monitor = SystemMonitor()
    result = monitor.update_state()

    print(f"CPU: {result['cpu_percent']:.1f}%")
    print(f"Memory: {result['memory_percent']:.1f}% ({result['memory_used']}/{result['memory_total']})")
    print(f"Uptime: {result['uptime']}")


if __name__ == "__main__":
    main()
