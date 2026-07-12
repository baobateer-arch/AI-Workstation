"""DeepSeek 余额监控器 - 调用官方 API 获取真实余额。

v1.3.0: 使用 GET /user/balance 获取余额数据。
v1.3.1: 自动加载项目根目录 .env 文件。
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.state_manager import state_manager


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 加载 .env 文件（系统环境变量优先）
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass


# DeepSeek API 配置
ENV_API_KEY = "DEEPSEEK_API_KEY"
BALANCE_URL = "https://api.deepseek.com/user/balance"

# 超时（秒）
REQUEST_TIMEOUT = 10


def _get_api_key() -> str | None:
    """从环境变量获取 API Key（系统环境变量 > .env）"""
    return os.environ.get(ENV_API_KEY)


def _fetch_balance(api_key: str) -> dict[str, Any]:
    """调用 DeepSeek Balance API

    Returns:
        dict: {balance, currency, is_available, raw}
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(
            BALANCE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # 解析响应
        is_available = data.get("is_available", False)
        balance_infos = data.get("balance_infos", [])

        if balance_infos:
            info = balance_infos[0]
            balance = float(info.get("total_balance", 0))
            currency = info.get("currency", "CNY")
        else:
            balance = 0.0
            currency = "CNY"

        return {
            "balance": balance,
            "currency": currency,
            "is_available": is_available,
            "raw": data,
        }

    except urllib.error.HTTPError as e:
        return {
            "balance": None,
            "currency": "CNY",
            "is_available": False,
            "error": f"HTTP {e.code}: {e.reason}",
        }
    except urllib.error.URLError as e:
        return {
            "balance": None,
            "currency": "CNY",
            "is_available": False,
            "error": f"Network error: {e.reason}",
        }
    except Exception as e:
        return {
            "balance": None,
            "currency": "CNY",
            "is_available": False,
            "error": str(e)[:100],
        }


def update_state() -> dict[str, Any]:
    """更新 DeepSeek 余额状态到 workstation_state.json。

    Returns:
        dict: {balance, currency, status, message, updated}
    """
    api_key = _get_api_key()

    # 未配置 API Key
    if not api_key:
        return {
            "balance": None,
            "currency": "CNY",
            "status": "NOT_CONFIGURED",
            "message": "DEEPSEEK_API_KEY not set",
            "updated": False,
        }

    # 调用 API
    result = _fetch_balance(api_key)

    # API 失败
    if result.get("error"):
        return {
            "balance": None,
            "currency": result["currency"],
            "status": "UNAVAILABLE",
            "message": result["error"],
            "updated": False,
        }

    # API 成功，更新状态
    state = state_manager.get_state()
    state.resource.deepseek_balance = result["balance"]
    state.resource.updated = datetime.now().isoformat()
    state_manager.save()

    return {
        "balance": result["balance"],
        "currency": result["currency"],
        "status": "OK",
        "message": f"{result['balance']:.2f} {result['currency']}",
        "updated": True,
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== DeepSeek Balance Monitor (v1.3.0) ===")
    print()

    api_key = _get_api_key()
    if not api_key:
        print("Status: NOT CONFIGURED")
        print("Message: DEEPSEEK_API_KEY environment variable not set")
        print()
        print("To configure:")
        print("  set DEEPSEEK_API_KEY=your_api_key")
        return

    print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
    print()

    result = update_state()

    print(f"Status: {result['status']}")
    if result["balance"] is not None:
        print(f"Balance: {result['balance']:.2f} {result['currency']}")
    print(f"Message: {result['message']}")


if __name__ == "__main__":
    main()
