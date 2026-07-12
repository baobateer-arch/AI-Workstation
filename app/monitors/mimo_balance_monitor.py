"""MiMo 余额监控器 - 调用官方 API 获取真实余额。

v1.3.0: 使用 GET /api/v1/balance 获取余额数据。
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


# MiMo API 配置
ENV_COOKIE = "MIMO_COOKIE"
BALANCE_URL = "https://platform.xiaomimimo.com/api/v1/balance"

# 超时（秒）
REQUEST_TIMEOUT = 10


def _get_cookie() -> str | None:
    """从环境变量获取 Cookie"""
    return os.environ.get(ENV_COOKIE)


def _fetch_balance(cookie: str) -> dict[str, Any]:
    """调用 MiMo Balance API

    Returns:
        dict: {balance, currency, raw}
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(
            BALANCE_URL,
            headers={
                "Cookie": cookie,
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # 解析响应
        balance_data = data.get("data", {})
        balance = float(balance_data.get("balance", 0))
        currency = balance_data.get("currency", "CNY")

        return {
            "balance": balance,
            "currency": currency,
            "raw": data,
        }

    except urllib.error.HTTPError as e:
        return {
            "balance": None,
            "currency": "CNY",
            "error": f"HTTP {e.code}: {e.reason}",
        }
    except urllib.error.URLError as e:
        return {
            "balance": None,
            "currency": "CNY",
            "error": f"Network error: {e.reason}",
        }
    except Exception as e:
        return {
            "balance": None,
            "currency": "CNY",
            "error": str(e)[:100],
        }


def update_state() -> dict[str, Any]:
    """更新 MiMo 余额状态到 workstation_state.json。

    Returns:
        dict: {balance, currency, status, message, updated}
    """
    cookie = _get_cookie()

    # 未配置 Cookie
    if not cookie:
        return {
            "balance": None,
            "currency": "CNY",
            "status": "NOT_CONFIGURED",
            "message": "MIMO_COOKIE not set",
            "updated": False,
        }

    # 调用 API
    result = _fetch_balance(cookie)

    # API 失败
    if result.get("error"):
        return {
            "balance": None,
            "currency": result["currency"],
            "status": "ERROR",
            "message": result["error"],
            "updated": False,
        }

    # API 成功，更新状态
    state = state_manager.get_state()
    state.resource.mimo_balance = result["balance"]
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
    print("=== MiMo Balance Monitor (v1.3.0) ===")
    print()

    cookie = _get_cookie()
    if not cookie:
        print("Status: NOT CONFIGURED")
        print("Message: MIMO_COOKIE environment variable not set")
        print()
        print("To configure:")
        print("  set MIMO_COOKIE=your_cookie_value")
        return

    print(f"Cookie: {cookie[:16]}...")
    print()

    result = update_state()

    print(f"Status: {result['status']}")
    if result["balance"] is not None:
        print(f"Balance: {result['balance']:.2f} {result['currency']}")
    print(f"Message: {result['message']}")


if __name__ == "__main__":
    main()
