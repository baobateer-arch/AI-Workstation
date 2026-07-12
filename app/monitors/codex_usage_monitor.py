"""Codex 使用量监控器。

v2.0.0: 从 Codex HTTP 响应头读取真实额度数据。
数据源：~/.codex/logs_2.sqlite → logs 表 → feedback_log_body 中的 x-codex-* headers。
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.state_manager import state_manager


# Codex 日志数据库路径
CODEX_LOGS_DB = Path.home() / ".codex" / "logs_2.sqlite"


def _read_codex_data() -> dict[str, Any]:
    """从 logs_2.sqlite 读取最新 Codex API 响应头中的额度数据。

    Returns:
        dict: {
            primary: {used_percent, remaining_percent, reset_at},
            secondary: {used_percent, remaining_percent, reset_at}
        }
        无数据返回空字典
    """
    if not CODEX_LOGS_DB.exists():
        return {}

    try:
        conn = sqlite3.connect(f"file:{CODEX_LOGS_DB}?mode=ro", uri=True)
        cursor = conn.cursor()

        # 查找最新的包含 x-codex 响应头的 API 响应日志
        cursor.execute("""
            SELECT feedback_log_body
            FROM logs
            WHERE target = 'codex_http_client::default_client'
              AND feedback_log_body LIKE '%x-codex-primary-used-percent%'
              AND feedback_log_body LIKE '%codex/responses%'
            ORDER BY ts DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return {}

        body = row[0]
        return _parse_codex_headers(body)

    except Exception:
        return {}


def _parse_codex_headers(body: str) -> dict[str, Any]:
    """从 feedback_log_body 中解析 x-codex-* 响应头。

    日志格式：headers={"key": "value", ...} （headers 无引号）

    Args:
        body: feedback_log_body 内容

    Returns:
        dict: {
            primary: {used_percent, reset_at},
            secondary: {used_percent, reset_at}
        }
    """
    # 提取 headers JSON 部分（在 headers={ 之后，headers 无引号）
    headers_match = re.search(r'headers\s*=\s*\{', body)
    if not headers_match:
        return {}

    # 从 headers 起始位置提取所有 key-value 对
    headers_str = body[headers_match.end():]

    # 用正则提取 x-codex-* 头部值
    def _extract_int(header_name: str) -> int | None:
        m = re.search(rf'"{re.escape(header_name)}"\s*:\s*"(\d+)"', headers_str)
        return int(m.group(1)) if m else None

    primary_used = _extract_int("x-codex-primary-used-percent")
    primary_reset = _extract_int("x-codex-primary-reset-at")
    secondary_used = _extract_int("x-codex-secondary-used-percent")
    secondary_reset = _extract_int("x-codex-secondary-reset-at")

    # 调试输出
    _debug_print(primary_used, primary_reset, secondary_used, secondary_reset)

    if primary_used is None and secondary_used is None:
        return {}

    result: dict[str, Any] = {}

    if primary_used is not None:
        result["primary"] = {
            "used_percent": primary_used,
            "remaining_percent": 100 - primary_used,
            "reset_at": primary_reset,
        }

    if secondary_used is not None:
        result["secondary"] = {
            "used_percent": secondary_used,
            "remaining_percent": 100 - secondary_used,
            "reset_at": secondary_reset,
        }

    return result


def _debug_print(
    primary_used: int | None,
    primary_reset: int | None,
    secondary_used: int | None,
    secondary_reset: int | None,
) -> None:
    """临时调试输出。"""
    try:
        print(f"[CodexMonitor DEBUG] primary.used_percent: {primary_used}")
        print(f"[CodexMonitor DEBUG] primary.reset_at: {primary_reset}")
        print(f"[CodexMonitor DEBUG] secondary.used_percent: {secondary_used}")
        print(f"[CodexMonitor DEBUG] secondary.reset_at: {secondary_reset}")
    except Exception:
        pass


def _format_reset_time(reset_at: int | None) -> str:
    """将 Unix 时间戳转换为本地时间 HH:MM 格式。"""
    if not reset_at:
        return ""
    try:
        dt = datetime.fromtimestamp(reset_at)
        return dt.strftime("%H:%M")
    except Exception:
        return ""


def _format_reset_date(reset_at: int | None) -> str:
    """将 Unix 时间戳转换为本地日期 MM/DD 格式。"""
    if not reset_at:
        return ""
    try:
        dt = datetime.fromtimestamp(reset_at)
        return dt.strftime("%m/%d")
    except Exception:
        return ""


def update_state() -> dict[str, Any]:
    """更新 Codex 使用量状态到 workstation_state.json。

    Returns:
        dict: {
            primary: {used_percent, remaining_percent, reset_time},
            secondary: {used_percent, remaining_percent, reset_date},
            status, updated
        }
    """
    data = _read_codex_data()

    if not data:
        return {
            "primary": None,
            "secondary": None,
            "status": "UNKNOWN",
            "updated": False,
        }

    primary_result = None
    if "primary" in data:
        primary_data = data["primary"]
        reset_time = _format_reset_time(primary_data.get("reset_at"))
        primary_result = {
            "used_percent": primary_data["used_percent"],
            "remaining_percent": primary_data["remaining_percent"],
            "reset_time": reset_time,
        }

    secondary_result = None
    if "secondary" in data:
        secondary_data = data["secondary"]
        reset_date = _format_reset_date(secondary_data.get("reset_at"))
        secondary_result = {
            "used_percent": secondary_data["used_percent"],
            "remaining_percent": secondary_data["remaining_percent"],
            "reset_date": reset_date,
        }

    # 更新状态
    state = state_manager.get_state()

    if primary_result:
        state.resource.codex_percent = float(primary_result["remaining_percent"])
        state.resource.codex_reset_at = primary_result["reset_time"]

    if secondary_result:
        state.resource.codex_weekly_percent = float(secondary_result["remaining_percent"])
        state.resource.codex_weekly_reset_at = secondary_result["reset_date"]

    state.resource.updated = datetime.now().isoformat()
    state_manager.save()

    return {
        "primary": primary_result,
        "secondary": secondary_result,
        "status": "OK" if primary_result or secondary_result else "UNKNOWN",
        "updated": True,
    }


# 全局监控器实例（兼容旧版导入）
codex_usage_monitor = type("CodexUsageMonitor", (), {"update_state": staticmethod(update_state)})()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Codex Usage Monitor (v2.0.0) ===")
    print(f"Data source: {CODEX_LOGS_DB}")
    print()

    data = _read_codex_data()
    if not data:
        print("Status: UNKNOWN")
        print("Message: No x-codex headers found in logs_2.sqlite")
        return

    if "primary" in data:
        primary = data["primary"]
        reset_time = _format_reset_time(primary.get("reset_at"))
        print(f"[5H] Used: {primary['used_percent']}%")
        print(f"[5H] Remaining: {primary['remaining_percent']}%")
        print(f"[5H] Reset: {reset_time}")
        print()

    if "secondary" in data:
        secondary = data["secondary"]
        reset_date = _format_reset_date(secondary.get("reset_at"))
        print(f"[7D] Used: {secondary['used_percent']}%")
        print(f"[7D] Remaining: {secondary['remaining_percent']}%")
        print(f"[7D] Reset: {reset_date}")
        print()

    print("Status: OK")


if __name__ == "__main__":
    main()
