"""DeepSeek 资源发现监控器。"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.state_manager import state_manager


# DeepSeek 相关环境变量
ENV_KEYS = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_KEY",
    "DS_API_KEY",
]

# 配置文件路径
CONFIG_PATHS = [
    Path.home() / ".deepseek" / "config.json",
    Path.home() / ".config" / "deepseek" / "config.json",
    Path(os.environ.get("APPDATA", "")) / "DeepSeek" / "config.json",
    Path.home() / ".env",
    Path(".env"),
]


class DeepSeekResourceMonitor:
    """DeepSeek 资源发现监控器"""

    def __init__(self):
        self._api_found = False
        self._balance: float | None = None
        self._daily_cost: float | None = None
        self._status: str = "UNKNOWN"

    def _check_environment(self) -> bool:
        """检查环境变量中是否有 API Key"""
        for key in ENV_KEYS:
            if os.environ.get(key):
                return True
        return False

    def _check_env_files(self) -> bool:
        """检查 .env 文件"""
        env_files = [
            Path.home() / ".env",
            Path(".env"),
            Path(".env.local"),
        ]

        for env_file in env_files:
            if env_file.exists():
                try:
                    content = env_file.read_text(encoding="utf-8")
                    for key in ENV_KEYS:
                        if key in content:
                            return True
                except Exception:
                    pass

        return False

    def _load_config(self) -> dict[str, Any]:
        """加载配置文件"""
        for config_path in CONFIG_PATHS:
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return {}

    def discover(self) -> dict[str, Any]:
        """
        发现 DeepSeek 资源。

        Returns:
            发现结果
        """
        # 检查 API Key
        self._api_found = self._check_environment() or self._check_env_files()

        # 尝试加载配置
        config = self._load_config()

        # 尝试提取余额和使用量
        # 注意：DeepSeek 可能没有本地配置文件存储余额信息
        balance = config.get("balance")
        daily_cost = config.get("daily_cost") or config.get("usage")

        if balance is not None:
            try:
                self._balance = float(balance)
            except (ValueError, TypeError):
                self._balance = None

        if daily_cost is not None:
            try:
                self._daily_cost = float(daily_cost)
            except (ValueError, TypeError):
                self._daily_cost = None

        # 确定状态
        if self._api_found:
            if self._balance is not None:
                self._status = "OK"
            else:
                self._status = "API_ONLY"
        else:
            self._status = "NOT_CONFIGURED"

        return {
            "api_found": self._api_found,
            "balance": self._balance,
            "daily_cost": self._daily_cost,
            "status": self._status,
        }

    def update_state(self) -> dict[str, Any]:
        """
        更新 DeepSeek 资源状态到 workstation_state.json。

        Returns:
            更新后的状态信息
        """
        try:
            result = self.discover()

            # 更新资源状态
            state = state_manager.get_state()

            if result["balance"] is not None:
                state.resource.deepseek_balance = result["balance"]

            state.resource.updated = datetime.now().isoformat()
            state_manager.save()

            return {
                "name": "DeepSeek",
                "api_found": result["api_found"],
                "balance": result["balance"],
                "daily_cost": result["daily_cost"],
                "status": result["status"],
                "updated": True,
            }

        except Exception as e:
            return {
                "name": "DeepSeek",
                "api_found": False,
                "balance": None,
                "daily_cost": None,
                "status": "ERROR",
                "error": str(e)[:100],
                "updated": False,
            }


# 全局监控器实例
deepseek_resource_monitor = DeepSeekResourceMonitor()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== DeepSeek Resource ===")
    print()

    monitor = DeepSeekResourceMonitor()
    result = monitor.update_state()

    api_str = "FOUND" if result['api_found'] else "NOT FOUND"
    balance_str = str(result['balance']) if result['balance'] is not None else "UNKNOWN"
    cost_str = str(result['daily_cost']) if result['daily_cost'] is not None else "UNKNOWN"

    print(f"API: {api_str}")
    print(f"Balance: {balance_str}")
    print(f"Usage: {cost_str}")
    print(f"Status: {result['status']}")


if __name__ == "__main__":
    main()
