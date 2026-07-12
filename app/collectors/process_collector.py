"""进程检测器 - 检测 Windows 进程。"""

from __future__ import annotations

import subprocess
import sys
from typing import Any


# 已知的进程名模式
PROCESS_PATTERNS = {
    "claude_running": ["claude.exe", "Claude.exe"],
    "vscode_running": ["Code.exe", "code.exe"],
    "codex_running": ["codex.exe", "Codex.exe"],
}


def _get_running_processes() -> list[str]:
    """获取当前运行的进程列表"""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            processes = []
            for line in lines:
                if line:
                    # CSV 格式: "进程名","PID","会话名","会话#","内存使用"
                    parts = line.split(",")
                    if parts:
                        name = parts[0].strip('"').lower()
                        processes.append(name)
            return processes
        else:
            # Linux/Mac
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            return [line.split()[-1].lower() for line in lines[1:] if line]
    except Exception:
        return []


def detect_processes() -> dict[str, bool]:
    """
    检测关键进程是否运行。

    Returns:
        dict: 包含各进程检测结果
    """
    running = _get_running_processes()
    running_set = set(running)

    result = {}
    for key, patterns in PROCESS_PATTERNS.items():
        found = any(p.lower() in running_set for p in patterns)
        result[key] = found

    return result


def get_process_info() -> dict[str, Any]:
    """获取详细的进程信息"""
    detection = detect_processes()
    return {
        "processes": detection,
        "claude_running": detection.get("claude_running", False),
        "vscode_running": detection.get("vscode_running", False),
        "codex_running": detection.get("codex_running", False),
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== 进程检测 ===")
    info = get_process_info()
    print(f"Claude 运行: {info['claude_running']}")
    print(f"VS Code 运行: {info['vscode_running']}")
    print(f"Codex 运行: {info['codex_running']}")


if __name__ == "__main__":
    main()
