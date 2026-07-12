"""AI Workstation 统一运行入口。"""

from __future__ import annotations

import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _print_header():
    """打印头部"""
    print("=== AI Workstation ===")
    print()


def _update_agents() -> dict[str, str]:
    """更新 Agent 状态（v1.2.0: 使用健康检测器获取真实状态）"""
    print("[Agent]")

    results = {}

    # 使用健康检测器获取真实状态
    try:
        from app.monitors.agent_health_checker import check_all
        health = check_all()

        # Claude: 使用健康检测器（进程+事件时间判断 RUNNING/IDLE/STOPPED）
        results["Claude"] = health["claude"]["status"]
        print(f"  Claude: {results['Claude']}")

        # Codex: 使用进程检测
        results["Codex"] = health["codex"]["status"]
        print(f"  Codex: {results['Codex']}")

        # MiMo: 使用进程检测
        results["MiMo"] = health["mimo"]["status"]
        print(f"  MiMo: {results['MiMo']}")

        # 更新 workstation_state.json
        from app.core.state_manager import state_manager
        from app.core.constants import AgentStatus

        # Claude
        state_manager.update_agent(
            agent_id="claude_code_vscode",
            status=AgentStatus.normalize(results["Claude"]),
            message=health["claude"]["message"],
            name="Claude Code",
            channel="VS Code",
            last_activity=health["claude"].get("last_activity", ""),
        )

        # Codex
        state_manager.update_agent(
            agent_id="codex_desktop",
            status=AgentStatus.normalize(results["Codex"]),
            message=health["codex"]["message"],
            name="Codex",
            channel="桌面端",
            last_activity=health["codex"].get("last_activity", ""),
        )

        # MiMo (PowerShell)
        state_manager.update_agent(
            agent_id="mimo_code_powershell",
            status=AgentStatus.normalize(results["MiMo"]),
            message=health["mimo"]["message"],
            name="MiMo Code",
            channel="PowerShell",
            last_activity=health["mimo"].get("last_activity", ""),
        )

        # MiMo (VS Code) - 同步状态
        state_manager.update_agent(
            agent_id="mimo_code_vscode",
            status=AgentStatus.normalize(results["MiMo"]),
            message=health["mimo"]["message"],
            name="MiMo Code",
            channel="VS Code",
            last_activity=health["mimo"].get("last_activity", ""),
        )

    except Exception as e:
        results["Claude"] = "ERROR"
        results["Codex"] = "ERROR"
        results["MiMo"] = "ERROR"
        print(f"  ERROR: {e}")

    print()
    return results


def _update_resources() -> dict[str, str]:
    """更新资源状态"""
    print("[Resource]")

    results = {}

    # Codex 5H 额度
    try:
        from app.monitors.codex_usage_monitor import codex_usage_monitor
        codex_usage_monitor.update_state()

        from app.core.state_manager import state_manager
        state = state_manager.get_state()
        codex_5h_percent = state.resource.codex_percent
        codex_7d_percent = state.resource.codex_weekly_percent
        results["Codex 5H"] = f"{codex_5h_percent:.0f}%"
        results["Codex 7D"] = f"{codex_7d_percent:.0f}%"
        print(f"  Codex 5H: {codex_5h_percent:.0f}%")
        print(f"  Codex 7D: {codex_7d_percent:.0f}%")
    except Exception as e:
        results["Codex 5H"] = "UNKNOWN"
        results["Codex 7D"] = "UNKNOWN"
        print(f"  Codex: UNKNOWN ({e})")

    # DeepSeek 余额 (v1.3.0: 调用官方 API)
    try:
        from app.monitors.deepseek_balance_monitor import update_state as ds_update
        ds_result = ds_update()

        if ds_result["updated"]:
            state = state_manager.get_state()
            deepseek_balance = state.resource.deepseek_balance
            results["DeepSeek"] = f"¥{deepseek_balance:.2f}"
            print(f"  DeepSeek: ¥{deepseek_balance:.2f}")
        else:
            results["DeepSeek"] = ds_result["status"]
            print(f"  DeepSeek: {ds_result['status']}")
    except Exception as e:
        results["DeepSeek"] = "UNKNOWN"
        print(f"  DeepSeek: UNKNOWN ({e})")

    # MiMo 余额 (v1.3.0: 调用官方 API)
    try:
        from app.monitors.mimo_balance_monitor import update_state as mimo_update
        mimo_result = mimo_update()

        if mimo_result["updated"]:
            state = state_manager.get_state()
            mimo_balance = state.resource.mimo_balance
            results["MiMo"] = f"¥{mimo_balance:.2f}"
            print(f"  MiMo: ¥{mimo_balance:.2f}")
        else:
            results["MiMo"] = mimo_result["status"]
            print(f"  MiMo: {mimo_result['status']}")
    except Exception as e:
        results["MiMo"] = "UNKNOWN"
        print(f"  MiMo: UNKNOWN ({e})")

    print()
    return results


def _build_dashboard() -> bool:
    """生成 dashboard.json"""
    print("[Dashboard]")

    try:
        from app.core.dashboard_builder import build_and_save
        dashboard = build_and_save()
        print("  dashboard.json updated")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def _generate_kindle() -> bool:
    """生成 Kindle 图片"""
    print("[Kindle]")

    try:
        from app.kindle_renderer import render_kindle_dashboard
        result = render_kindle_dashboard()
        print(f"  dashboard_kindle.png generated")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    """主函数"""
    _print_header()

    # 1. 更新 Agent 状态
    _update_agents()

    # 2. 更新资源状态
    _update_resources()

    # 3. 生成 dashboard.json
    dashboard_ok = _build_dashboard()

    # 4. 生成 Kindle 图片
    kindle_ok = _generate_kindle()

    # 返回状态
    if dashboard_ok and kindle_ok:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
