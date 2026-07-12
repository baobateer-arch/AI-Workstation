"""VPN 状态监控 - 读取 v2rayN 数据库获取流量和到期信息。"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path


# v2rayN 路径
V2RAYN_DIR = Path.home() / "Downloads" / "v2rayN-windows-64-desktop" / "v2rayN-windows-64"
V2RAYN_DB = V2RAYN_DIR / "guiConfigs" / "guiNDB.db"
V2RAYN_CONFIG = V2RAYN_DIR / "guiConfigs" / "guiNConfig.json"


def _check_v2rayn_running() -> bool:
    """检查 v2rayN 是否运行"""
    import subprocess
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq v2rayN.exe"],
            capture_output=True, text=True, timeout=5
        )
        return "v2rayN.exe" in result.stdout
    except Exception:
        return False


def _get_active_node_id() -> str:
    """从 guiNConfig.json 获取活动节点 ID"""
    if not V2RAYN_CONFIG.exists():
        return ""
    try:
        with open(V2RAYN_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("IndexId", "")
    except Exception:
        return ""


def _get_node_name(cursor: sqlite3.Cursor, node_id: str) -> str:
    """获取节点名称"""
    if not node_id:
        return ""
    cursor.execute("SELECT Remarks FROM ProfileItem WHERE IndexId = ?", (node_id,))
    row = cursor.fetchone()
    return row[0] if row and row[0] else ""


def _get_routing_mode(cursor: sqlite3.Cursor) -> str:
    """获取路由模式"""
    cursor.execute("SELECT Remarks FROM RoutingItem WHERE IsActive = 1")
    row = cursor.fetchone()
    if row and row[0]:
        return row[0]
    cursor.execute("SELECT Remarks FROM RoutingItem WHERE Enabled = 1 LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row and row[0] else ""


def read_vpn_status() -> dict[str, str]:
    """从 v2rayN 读取 VPN 完整状态。

    Returns:
        {
            "status": "CONNECTED" | "DISCONNECTED",
            "node": "美国 2 CN2 GIA 顶级路线 x4",
            "routing": "V4-绕过大陆(Whitelist)",
            "remaining": "19.43 GB",
            "expiry": "2053-09-03"
        }
    """
    result = {
        "status": "DISCONNECTED",
        "node": "",
        "routing": "",
        "remaining": "",
        "expiry": "",
    }

    # 检查 v2rayN 是否运行
    result["status"] = "CONNECTED" if _check_v2rayn_running() else "DISCONNECTED"

    if not V2RAYN_DB.exists():
        return result

    try:
        conn = sqlite3.connect(str(V2RAYN_DB))
        cursor = conn.cursor()

        # 获取活动节点名称
        node_id = _get_active_node_id()
        result["node"] = _get_node_name(cursor, node_id)

        # 获取路由模式
        result["routing"] = _get_routing_mode(cursor)

        # 获取剩余流量
        cursor.execute("SELECT Remarks FROM ProfileItem WHERE Remarks LIKE '%剩余流量%'")
        row = cursor.fetchone()
        if row and row[0]:
            match = re.search(r"剩余流量[：:]\s*([\d.]+)\s*(GB|MB|TB)", row[0])
            if match:
                result["remaining"] = f"{match.group(1)} {match.group(2)}"

        # 获取到期时间
        cursor.execute("SELECT Remarks FROM ProfileItem WHERE Remarks LIKE '%套餐到期%'")
        row = cursor.fetchone()
        if row and row[0]:
            match = re.search(r"套餐到期[：:]\s*([\d-]+)", row[0])
            if match:
                result["expiry"] = match.group(1)

        conn.close()
    except Exception:
        pass

    return result
