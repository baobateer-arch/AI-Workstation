"""Claude 使用量收集器。"""

from __future__ import annotations

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Any

from app.core.state_manager import state_manager


# Claude 数据文件路径
CLAUDE_DATA_PATH = Path.home() / ".claude.json"

# 默认汇率
DEFAULT_USD_TO_CNY = 7.2


class ClaudeUsageCollector:
    """Claude 使用量收集器"""

    def __init__(self, usd_to_cny: float = DEFAULT_USD_TO_CNY):
        self._usd_to_cny = usd_to_cny
        self._today_cost_usd: float = 0.0
        self._today_tokens: int = 0
        self._today_input: int = 0
        self._today_output: int = 0

    def _load_data(self) -> dict[str, Any]:
        """加载 Claude 数据文件"""
        if not CLAUDE_DATA_PATH.exists():
            return {}

        try:
            with open(CLAUDE_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _extract_today_usage(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        提取今日使用量。

        注意：Claude 数据格式可能变化，这里尝试常见字段。
        不读取 API Key 和 Token。
        """
        today = date.today().isoformat()

        # 尝试从不同的数据结构中提取
        usage = data.get("usage", {})
        daily = usage.get("daily", [])
        sessions = data.get("sessions", [])

        today_cost = 0.0
        today_input = 0
        today_output = 0

        # 尝试从 daily 数据提取
        if isinstance(daily, list):
            for day in daily:
                if day.get("date") == today:
                    today_cost = float(day.get("costUSD", 0) or day.get("cost", 0) or 0)
                    today_input = int(day.get("inputTokens", 0) or day.get("input_tokens", 0) or 0)
                    today_output = int(day.get("outputTokens", 0) or day.get("output_tokens", 0) or 0)
                    break

        # 尝试从 sessions 数据提取
        if today_cost == 0 and isinstance(sessions, list):
            for session in sessions:
                session_date = session.get("date", "")[:10]
                if session_date == today:
                    today_cost += float(session.get("costUSD", 0) or session.get("cost", 0) or 0)
                    today_input += int(session.get("inputTokens", 0) or session.get("input_tokens", 0) or 0)
                    today_output += int(session.get("outputTokens", 0) or session.get("output_tokens", 0) or 0)

        self._today_cost_usd = today_cost
        self._today_input = today_input
        self._today_output = today_output
        self._today_tokens = today_input + today_output

        return {
            "cost_usd": today_cost,
            "cost_cny": today_cost * self._usd_to_cny,
            "input_tokens": today_input,
            "output_tokens": today_output,
            "total_tokens": today_input + today_output,
        }

    def collect(self) -> dict[str, Any]:
        """
        收集 Claude 使用量。

        Returns:
            收集结果
        """
        data = self._load_data()
        usage = self._extract_today_usage(data)

        return {
            "daily_cost": usage["cost_cny"],
            "daily_cost_usd": usage["cost_usd"],
            "tokens": usage["total_tokens"],
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "source": "claude_usage",
        }

    def update_state(self) -> dict[str, Any]:
        """
        更新 Claude 使用量状态到 workstation_state.json。

        Returns:
            更新后的状态信息
        """
        try:
            usage = self.collect()

            # 更新资源状态（写入 deepseek 字段，因为 Claude 和 DeepSeek 都是 AI 服务）
            state = state_manager.get_state()

            state.resource.deepseek_balance = state.resource.deepseek_balance  # 保持原有余额
            state.resource.updated = datetime.now().isoformat()
            state_manager.save()

            # 同时更新 agent 状态
            state_manager.update_agent(
                agent_id="claude_usage",
                status="RUNNING",
                message=f"今日消耗: ${usage['daily_cost_usd']:.2f}",
                name="Claude",
                channel="Usage",
            )

            return {
                "name": "Claude",
                "daily_cost": usage["daily_cost"],
                "daily_cost_usd": usage["daily_cost_usd"],
                "tokens": usage["tokens"],
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "source": usage["source"],
                "updated": True,
            }

        except Exception as e:
            return {
                "name": "Claude",
                "daily_cost": None,
                "tokens": None,
                "source": "claude_usage",
                "status": "ERROR",
                "error": str(e)[:100],
                "updated": False,
            }


# 全局收集器实例
claude_usage_collector = ClaudeUsageCollector()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Claude Usage ===")
    print()

    collector = ClaudeUsageCollector()
    result = collector.update_state()

    cost_str = f"${result['daily_cost_usd']:.2f}" if result['daily_cost_usd'] else "N/A"
    tokens_str = str(result['tokens']) if result['tokens'] else "N/A"

    print(f"Today Cost: {cost_str}")
    print(f"Tokens: {tokens_str}")
    print(f"State Updated: {'YES' if result['updated'] else 'NO'}")


if __name__ == "__main__":
    main()
