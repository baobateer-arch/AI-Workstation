"""Kindle 设备检测器。"""

from __future__ import annotations

import os
import string
from pathlib import Path
from typing import Any


# Kindle 目录结构
KINDLE_DIRS = ["documents", "screensavers"]


def get_removable_drives() -> list[str]:
    """获取可移动磁盘列表"""
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            # 检查是否是可移动磁盘
            try:
                import ctypes
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                # DRIVE_REMOVABLE = 2
                if drive_type == 2:
                    drives.append(letter)
            except Exception:
                pass
    return drives


def check_kindle_drive(drive: str) -> dict[str, Any]:
    """
    检查指定磁盘是否是 Kindle。

    Args:
        drive: 盘符字母（如 "E"）

    Returns:
        检查结果
    """
    drive_path = Path(f"{drive}:\\")

    if not drive_path.exists():
        return {
            "found": False,
            "drive": f"{drive}:",
            "target": False,
            "dirs": [],
        }

    # 检查 Kindle 目录
    found_dirs = []
    for dir_name in KINDLE_DIRS:
        if (drive_path / dir_name).is_dir():
            found_dirs.append(dir_name)

    is_kindle = len(found_dirs) >= 1  # 至少存在一个目录

    return {
        "found": True,
        "drive": f"{drive}:",
        "target": is_kindle,
        "dirs": found_dirs,
    }


def detect_kindle() -> dict[str, Any]:
    """
    检测 Kindle 设备。

    Returns:
        检测结果
    """
    # 获取可移动磁盘
    removable_drives = get_removable_drives()

    # 检查每个可移动磁盘
    for drive in removable_drives:
        result = check_kindle_drive(drive)
        if result["found"]:
            return {
                "device": "FOUND",
                "drive": result["drive"],
                "target": "OK" if result["target"] else "NOT FOUND",
                "dirs": result["dirs"],
            }

    return {
        "device": "NOT FOUND",
        "drive": "N/A",
        "target": "NOT FOUND",
        "dirs": [],
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Kindle Detector ===")
    print()

    result = detect_kindle()

    print(f"Device: {result['device']}")
    print(f"Drive: {result['drive']}")
    print(f"Target: {result['target']}")

    if result["dirs"]:
        print(f"Dirs: {', '.join(result['dirs'])}")


if __name__ == "__main__":
    main()
