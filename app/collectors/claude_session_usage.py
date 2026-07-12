"""Claude Session 使用量收集器。"""

from __future__ import annotations

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Any

from app.core.state_manager import state_manager


# Claude 数据目录
CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
SESSIONS_DIR = CLAUDE_DIR / "sessions"

# 默认汇率
DEFAULT_USD_TO_CNY = 7.2


class ClaudeSessionUsage:
    """Claude Session 使用量收集器"""

    def __init__(self, usd_to_cny: float = DEFAULT_USD_TO_CNY):
        self._usd_to_cny = usd_to_cny
        self._session_count = 0
        self._today_tokens = 0
        self._today_cost_usd = 0.0

    def _scan_directory(self, directory: Path) -> list[Path]:
        """扫描目录下的所有 json/jsonl 文件"""
        files = []
        if not directory.exists():
            return files

        try:
            for item in directory.rglob("*"):
                if item.is_file() and item.suffix in (".json", ".jsonl"):
                    files.append(item)
        except Exception:
            pass

        return files

    def _parse_jsonl(self, file_path: Path) -> list[dict]:
        """解析 JSONL 文件"""
        entries = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
        return entries

    def _parse_json(self, file_path: Path) -> dict | list:
        """解析 JSON 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _extract_usage_from_entry(self, entry: dict) -> dict[str, Any]:
        """
        从单条记录中提取使用量。

        安全：不提取 API Key、完整对话、用户输入内容。
        """
        result = {
            "timestamp": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "model": "",
            "cost": 0.0,
        }

        # 提取时间戳
        ts = entry.get("timestamp") or entry.get("created_at") or entry.get("time")
        if ts:
            result["timestamp"] = str(ts)

        # 提取 token 使用量
        usage = entry.get("usage", {})
        if isinstance(usage, dict):
            result["input_tokens"] = int(usage.get("input_tokens", 0) or usage.get("inputTokens", 0) or 0)
            result["output_tokens"] = int(usage.get("output_tokens", 0) or usage.get("outputTokens", 0) or 0)

        # 提取模型
        result["model"] = str(entry.get("model", ""))

        # 提取费用
        result["cost"] = float(entry.get("cost", 0) or entry.get("costUSD", 0) or 0)

        return result

    def _is_today(self, timestamp: str | None) -> bool:
        """检查时间戳是否是今天"""
        if not timestamp:
            return False

        try:
            # 尝试解析不同格式的时间戳
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(timestamp[:19], fmt)
                    return dt.date() == date.today()
                except ValueError:
                    continue

            # 尝试 ISO 格式
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.date() == date.today()

        except Exception:
            return False

    def collect(self) -> dict[str, Any]:
        """
        收集 Claude Session 使用量。

        Returns:
            收集结果
        """
        self._session_count = 0
        self._today_tokens = 0
        self._today_cost_usd = 0.0

        # 扫描所有文件
        all_files = []
        all_files.extend(self._scan_directory(PROJECTS_DIR))
        all_files.extend(self._scan_directory(SESSIONS_DIR))

        # 处理每个文件
        for file_path in all_files:
            try:
                if file_path.suffix == ".jsonl":
                    entries = self._parse_jsonl(file_path)
                    for entry in entries:
                        self._session_count += 1
                        usage = self._extract_usage_from_entry(entry)

                        if self._is_today(usage["timestamp"]):
                            self._today_tokens += usage["input_tokens"] + usage["output_tokens"]
                            self._today_cost_usd += usage["cost"]

                elif file_path.suffix == ".json":
                    data = self._parse_json(file_path)
                    if isinstance(data, list):
                        for entry in data:
                            self._session_count += 1
                            usage = self._extract_usage_from_entry(entry)

                            if self._is_today(usage["timestamp"]):
                                self._today_tokens += usage["input_tokens"] + usage["output_tokens"]
                                self._today_cost_usd += usage["cost"]
                    elif isinstance(data, dict):
                        self._session_count += 1
                        usage = self._extract_usage_from_entry(data)

                        if self._is_today(usage["timestamp"]):
                            self._today_tokens += usage["input_tokens"] + usage["output_tokens"]
                            self._today_cost_usd += usage["cost"]

            except Exception:
                continue

        return {
            "session_count": self._session_count,
            "today_tokens": self._today_tokens,
            "today_cost_usd": self._today_cost_usd,
            "today_cost_cny": self._today_cost_usd * self._usd_to_cny,
        }

    def update_state(self) -> dict[str, Any]:
        """
        更新 Claude Session 使用量状态到 workstation_state.json。

        Returns:
            更新后的状态信息
        """
        try:
            usage = self.collect()

            # 更新资源状态
            state = state_manager.get_state()
            state.resource.updated = datetime.now().isoformat()
            state_manager.save()

            return {
                "name": "Claude",
                "sessions": usage["session_count"],
                "today_tokens": usage["today_tokens"],
                "today_cost_usd": usage["today_cost_usd"],
                "today_cost_cny": usage["today_cost_cny"],
                "source": "claude_sessions",
                "updated": True,
            }

        except Exception as e:
            return {
                "name": "Claude",
                "sessions": 0,
                "today_tokens": 0,
                "today_cost_usd": 0,
                "today_cost_cny": 0,
                "source": "claude_sessions",
                "status": "ERROR",
                "error": str(e)[:100],
                "updated": False,
            }


# 全局收集器实例
claude_session_usage = ClaudeSessionUsage()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Claude Session Usage ===")
    print()

    collector = ClaudeSessionUsage()
    result = collector.update_state()

    print(f"Sessions: {result['sessions']}")
    print(f"Today Tokens: {result['today_tokens']}")
    print(f"Today Cost: ${result['today_cost_usd']:.2f}")
    print(f"State Updated: {'YES' if result['updated'] else 'NO'}")


if __name__ == "__main__":
    main()
