"""Agent 心跳管理 - 生命周期监控。"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


# 数据目录
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HEARTBEAT_FILE = DATA_DIR / "agent_heartbeat.json"

# 超时规则（秒）
TIMEOUTS = {
    "RUNNING": 5 * 60,      # 5分钟
    "WAITING": 30 * 60,     # 30分钟
    "PERMISSION": 60 * 60,  # 60分钟
}


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_heartbeat() -> dict[str, Any]:
    """加载心跳数据"""
    _ensure_data_dir()
    if HEARTBEAT_FILE.exists():
        try:
            with open(HEARTBEAT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_heartbeat(data: dict[str, Any]) -> None:
    """保存心跳数据"""
    _ensure_data_dir()
    with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_heartbeat(agent_id: str) -> dict[str, Any]:
    """
    更新 Agent 心跳时间。

    Args:
        agent_id: Agent 标识符

    Returns:
        更新后的心跳信息
    """
    heartbeat = _load_heartbeat()

    entry = {
        "last_seen": datetime.now().isoformat(),
        "stale": False,
    }

    heartbeat[agent_id] = entry
    _save_heartbeat(heartbeat)

    return entry


def get_heartbeat(agent_id: str) -> dict[str, Any] | None:
    """获取 Agent 心跳"""
    heartbeat = _load_heartbeat()
    return heartbeat.get(agent_id)


def check_stale_agents() -> list[dict[str, Any]]:
    """
    检测过期 Agent。

    Returns:
        过期 Agent 列表
    """
    from app.agent_runtime import get_all_runtime_statuses

    heartbeat = _load_heartbeat()
    runtime = get_all_runtime_statuses()
    now = datetime.now()
    stale_agents = []

    for agent_id, status_info in runtime.items():
        status = status_info.get("status", "")
        hb = heartbeat.get(agent_id, {})
        last_seen_str = hb.get("last_seen")

        if not last_seen_str:
            continue

        try:
            last_seen = datetime.fromisoformat(last_seen_str)
        except (ValueError, TypeError):
            continue

        elapsed = (now - last_seen).total_seconds()
        timeout = TIMEOUTS.get(status)

        if timeout and elapsed > timeout:
            stale_info = {
                "agent_id": agent_id,
                "status": status,
                "elapsed_seconds": int(elapsed),
                "timeout_seconds": timeout,
                "last_seen": last_seen_str,
            }

            if status == "RUNNING":
                # RUNNING 超时 -> UNKNOWN
                stale_info["action"] = "SET_UNKNOWN"
            else:
                # WAITING/PERMISSION 超时 -> 标记 stale
                stale_info["action"] = "MARK_STALE"
                stale_info["stale"] = True

            stale_agents.append(stale_info)

    return stale_agents


def apply_stale_updates() -> list[dict[str, Any]]:
    """
    应用过期更新。

    Returns:
        已更新的 Agent 列表
    """
    from app.agent_runtime import update_agent_status

    stale_agents = check_stale_agents()
    updated = []

    for agent in stale_agents:
        agent_id = agent["agent_id"]

        if agent["action"] == "SET_UNKNOWN":
            update_agent_status(
                agent_id=agent_id,
                status="UNKNOWN",
                message=f"超时 {agent['elapsed_seconds']//60} 分钟，状态未知",
            )
            updated.append(agent_id)
        elif agent["action"] == "MARK_STALE":
            # 更新心跳标记
            heartbeat = _load_heartbeat()
            if agent_id in heartbeat:
                heartbeat[agent_id]["stale"] = True
                _save_heartbeat(heartbeat)
            updated.append(agent_id)

    return updated


def get_agent_health(agent_id: str) -> dict[str, Any]:
    """
    获取 Agent 健康状态。

    Returns:
        dict: 包含健康信息
    """
    from app.agent_runtime import get_agent_status

    status_info = get_agent_status(agent_id)
    hb = get_heartbeat(agent_id)

    if not status_info:
        return {"status": "UNKNOWN", "healthy": False}

    status = status_info.get("status", "")
    stale = hb.get("stale", False) if hb else False
    last_seen = hb.get("last_seen") if hb else None

    # 计算健康度
    healthy = not stale and status != "UNKNOWN"

    return {
        "status": status,
        "healthy": healthy,
        "stale": stale,
        "last_seen": last_seen,
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m app.agent_heartbeat <command> [agent_id]")
        print()
        print("命令:")
        print("  update <agent_id>    更新心跳")
        print("  check                检测过期 Agent")
        print("  apply                应用过期更新")
        print("  health <agent_id>    查看健康状态")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "update" and len(sys.argv) > 2:
        result = update_heartbeat(sys.argv[2])
        print(f"[OK] 心跳已更新: {result}")

    elif cmd == "check":
        stale = check_stale_agents()
        if stale:
            print(f"[WARN] 发现 {len(stale)} 个过期 Agent:")
            for agent in stale:
                print(f"  - {agent['agent_id']}: {agent['action']}")
        else:
            print("[OK] 无过期 Agent")

    elif cmd == "apply":
        updated = apply_stale_updates()
        if updated:
            print(f"[OK] 已更新 {len(updated)} 个 Agent")
        else:
            print("[OK] 无需更新")

    elif cmd == "health" and len(sys.argv) > 2:
        health = get_agent_health(sys.argv[2])
        print(f"[OK] 健康状态: {health}")

    else:
        print("[ERROR] 无效命令")


if __name__ == "__main__":
    main()
