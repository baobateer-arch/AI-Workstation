"""日志读取器 - 读取 Claude Code 日志。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def read_logs(
    path: str | Path,
    max_lines: int = 100,
    encoding: str = "utf-8",
) -> dict[str, Any]:
    """
    读取日志文件。

    Args:
        path: 日志文件路径
        max_lines: 最大读取行数
        encoding: 文件编码

    Returns:
        dict: 包含日志内容和元信息
    """
    log_path = Path(path)

    if not log_path.exists():
        return {
            "exists": False,
            "lines": [],
            "total_lines": 0,
            "path": str(log_path),
        }

    try:
        with open(log_path, "r", encoding=encoding, errors="ignore") as f:
            all_lines = f.readlines()

        total = len(all_lines)
        lines = [line.rstrip() for line in all_lines[-max_lines:]]

        return {
            "exists": True,
            "lines": lines,
            "total_lines": total,
            "path": str(log_path),
        }
    except Exception as e:
        return {
            "exists": True,
            "error": str(e),
            "lines": [],
            "total_lines": 0,
            "path": str(log_path),
        }


def find_log_files(
    base_dir: str | Path,
    pattern: str = "*.log",
) -> list[Path]:
    """查找日志文件"""
    base = Path(base_dir)
    if not base.exists():
        return []
    return list(base.glob(pattern))


# 常见的日志路径（Claude Code）
DEFAULT_LOG_PATHS = [
    Path.home() / ".claude" / "logs",
    Path.home() / ".config" / "claude" / "logs",
    Path(os.environ.get("APPDATA", "")) / "Claude" / "logs",
]
