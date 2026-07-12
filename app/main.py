"""Entry point: generate dashboard and agent status PNGs."""

import sys
import os
import json
import sqlite3
from pathlib import Path
from typing import Any

from app.agent_sample_data import AGENT_SAMPLE_DATA
from app.agent_renderer import render_agent_status
from app.agent_models import AgentDashboardData

# v0.6
from app.v06_renderer import render_v06
from app.v05_sample_data import V05_SAMPLE_DATA

# Agent runtime 数据
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RUNTIME_FILE = DATA_DIR / "agent_runtime.json"

# CC Switch 数据库路径
CC_SWITCH_DB = Path(os.path.expanduser("~")) / ".cc-switch" / "cc-switch.db"
CLAUDE_SETTINGS = Path(os.path.expanduser("~")) / ".claude" / "settings.json"


def load_agent_runtime() -> dict[str, Any]:
    """加载 agent_runtime.json，如果不存在返回空字典"""
    try:
        if RUNTIME_FILE.exists():
            with open(RUNTIME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def get_cc_model_info() -> dict[str, str]:
    """获取 Claude Code 当前模型信息。

    优先级:
    1. CC Switch DB - 当前启用的 Provider 和 Model
    2. settings.json - ANTHROPIC_MODEL
    """
    result = {"provider": "", "model": ""}

    # 第一优先：读取 CC Switch DB
    if CC_SWITCH_DB.exists():
        try:
            conn = sqlite3.connect(str(CC_SWITCH_DB))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, settings_config FROM providers "
                "WHERE app_type='claude' AND is_current=1"
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                result["provider"] = row[0] or ""
                try:
                    config = json.loads(row[1] or "{}")
                    env = config.get("env", {})
                    result["model"] = env.get("ANTHROPIC_MODEL", "")
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

    # 第二优先：读取 settings.json
    if not result["model"] and CLAUDE_SETTINGS.exists():
        try:
            settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
            result["model"] = settings.get("env", {}).get("ANTHROPIC_MODEL", "")
        except Exception:
            pass

    return result


def adapt_data_for_v06(data: dict, runtime: dict[str, Any]) -> dict:
    """将 v05 数据结构适配为 v06 所需的扁平格式。"""
    goal = data.get("daily_goal", {})
    resource = data.get("ai_resource", {})

    # 获取 Claude Code 模型信息
    cc_info = get_cc_model_info()

    # 从 runtime 提取 Agent 信息
    agents = []
    needs_attention = 0
    running_count = 0

    for agent_id, agent_data in runtime.items():
        status = agent_data.get("status", "IDLE")
        agents.append({
            "id": agent_id,
            "name": agent_data.get("name", agent_id),
            "channel": agent_data.get("channel", "unknown"),
            "status": status,
            "message": agent_data.get("message", ""),
        })

        # 统计状态
        if status in ("PERMISSION", "WAITING", "ERROR"):
            needs_attention += 1
        elif status == "RUNNING":
            running_count += 1

    # 获取需要关注的 Agent 名称
    attention_agents = [
        a["name"] for a in agents
        if a["status"] in ("PERMISSION", "WAITING", "ERROR")
    ]

    return {
        "agent_attention": needs_attention,
        "attention_agents": attention_agents if attention_agents else ["无"],
        "agent_running": running_count,
        "agents": agents,
        "income": float(data.get("today_income", 0)),
        "completed": int(goal.get("completed", 0)),
        "target": int(goal.get("target", 5)),
        "avg_time": int(goal.get("avg_minutes", 0)),
        "cc_provider": cc_info["provider"],
        "cc_model": cc_info["model"],
        "codex_5h": f"{resource.get('codex_percent', 0):.0f}%",
        "codex_7d": f"{resource.get('codex_weekly_percent', 0):.0f}%",
        "deepseek": f"¥{resource.get('deepseek_balance', 0):.0f}",
        "mimo": f"¥{resource.get('mimo_balance', 0):.0f}",
        "suggestions": data.get("suggestions", []),
    }


def main():
    output_dir = os.path.join("output", "")
    os.makedirs(output_dir, exist_ok=True)

    ok = True

    # 1. 生成首页 (v0.6)
    try:
        # 加载 runtime 数据
        runtime = load_agent_runtime()
        v06_data = adapt_data_for_v06(V05_SAMPLE_DATA, runtime)
        result = render_v06(v06_data, os.path.join("output", "dashboard.png"))
        abs_path = str(result)
        print(f"[OK] 工作台图片生成成功")
        print(f"     {abs_path}")
    except Exception as e:
        print(f"[ERROR] 工作台生成失败: {e}", file=sys.stderr)
        ok = False

    # 2. 生成 Agent 值守台
    try:
        agent_data = AgentDashboardData.from_dict(AGENT_SAMPLE_DATA)
        result = render_agent_status(agent_data, os.path.join("output", "agent_status.png"))
        abs_path = str(result)
        print(f"[OK] Agent 值守台生成成功")
        print(f"     {abs_path}")
    except Exception as e:
        print(f"[ERROR] Agent 值守台生成失败: {e}", file=sys.stderr)
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
