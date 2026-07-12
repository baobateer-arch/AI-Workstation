"""Dashboard 构建器 - 生成 Kindle 最终展示数据模型。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.state_manager import state_manager
from app.core.agent_aggregator import aggregate_agents
from app.core.resource_aggregator import aggregate_resources
from app.core.cc_switch_reader import read_cc_model_info
from app.monitors.system_monitor import system_monitor


# 输出路径
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DASHBOARD_FILE = DATA_DIR / "dashboard.json"

# 只显示这三个 Agent
DISPLAY_AGENTS = ["claude", "codex", "mimo"]

# Agent 名称映射（首字母大写）
AGENT_NAMES = {
    "claude": "Claude",
    "codex": "Codex",
    "mimo": "MiMo",
}

# 需要关注的状态
ATTENTION_STATUSES = {"ERROR", "PERMISSION"}


def _format_relative_time(value: str) -> str:
    """将时间字符串格式化为相对时间格式。

    支持:
      - ISO 格式 (2026-07-12T09:45:04.870065) → "12 min ago"
      - 相对格式 (12 min ago) → 原样返回
      - 空字符串 → ""
    """
    if not value:
        return ""

    # 如果已经是相对格式，直接返回
    if "ago" in value or value == "just now":
        return value

    # 尝试解析 ISO 格式
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        dt_local = dt.replace(tzinfo=None)
        elapsed = (datetime.now() - dt_local).total_seconds()

        if elapsed < 60:
            return "just now"
        if elapsed < 3600:
            minutes = int(elapsed // 60)
            return f"{minutes} min ago"
        if elapsed < 86400:
            hours = int(elapsed // 3600)
            return f"{hours} hours ago"
        days = int(elapsed // 86400)
        return f"{days} days ago"
    except (ValueError, TypeError):
        return ""


def _format_running_time(started_at: str | None) -> str:
    """计算运行时间"""
    if not started_at:
        return "未运行"

    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
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


def build_dashboard() -> dict[str, Any]:
    """
    构建 Dashboard 数据。

    Returns:
        Dashboard 数据字典
    """
    state = state_manager.get_state()

    # 聚合 Agent
    aggregated_agents = aggregate_agents()
    agents = []

    for agent_id in DISPLAY_AGENTS:
        agent = aggregated_agents.get(agent_id)
        if agent:
            # 判断是否需要关注
            attention = agent.status in ATTENTION_STATUSES

            # 使用映射的名称
            display_name = AGENT_NAMES.get(agent_id, agent.name)

            # 获取 last_activity（从第一个实例）并格式化为相对时间
            last_activity = ""
            if agent.instances:
                raw_activity = agent.instances[0].get("last_activity", "")
                last_activity = _format_relative_time(raw_activity)

            agents.append({
                "name": display_name,
                "status": agent.status,
                "message": agent.message,
                "attention": attention,
                "last_activity": last_activity,
            })

    # 聚合资源
    aggregated_resources = aggregate_resources()
    resources = [
        {
            "title": item.title,
            "value": item.value,
            "detail": item.detail,
            "status": item.status,
        }
        for item in aggregated_resources.values()
    ]

    # 项目信息
    project = state.project

    # 计算运行时间（短格式）
    if project.name:
        running_time = _format_running_time(project.updated)
    else:
        running_time = "00:00"

    project_data = {
        "name": project.name or "无项目",
        "started_at": project.updated or "",
        "running_time": running_time,
        "cost": project.ai_cost,
    }

    # CC 模型信息（优先从 CC Switch 读取，fallback 到 state）
    cc_info = read_cc_model_info()
    if not cc_info["model"]:
        cc_info["provider"] = state.cc_model.provider
        cc_info["model"] = state.cc_model.model

    # 系统状态
    system_status = system_monitor.update_state()

    return {
        "agents": agents,
        "resources": resources,
        "project": project_data,
        "cc_model": cc_info,
        "system": system_status,
    }


def save_dashboard(dashboard: dict[str, Any]) -> Path:
    """
    保存 Dashboard 数据到 JSON 文件。

    Args:
        dashboard: Dashboard 数据

    Returns:
        输出文件路径
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)

    return DASHBOARD_FILE


def build_and_save() -> dict[str, Any]:
    """
    构建并保存 Dashboard 数据。

    Returns:
        Dashboard 数据
    """
    dashboard = build_dashboard()
    save_dashboard(dashboard)
    return dashboard


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Dashboard ===")
    print()

    dashboard = build_and_save()

    print("Agents:")
    for agent in dashboard['agents']:
        attention_str = " [!]" if agent['attention'] else ""
        print(f"  {agent['name']}: {agent['status']}{attention_str}")
    print()
    print(f"Project: {dashboard['project']['name']}")
    print(f"Running: {dashboard['project']['running_time']}")


if __name__ == "__main__":
    main()
