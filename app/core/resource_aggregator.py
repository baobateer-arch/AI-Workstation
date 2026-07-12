"""资源聚合层 - 统一展示资源信息。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.state_manager import state_manager


@dataclass
class ResourceItem:
    """资源项"""
    title: str
    value: str
    detail: str = ""
    status: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "value": self.value,
            "detail": self.detail,
            "status": self.status,
        }


def _format_quota(quota: float | None) -> tuple[str, str, str]:
    """格式化额度信息"""
    if quota is None:
        return ("UNKNOWN", "额度未知", "UNKNOWN")

    return (f"{quota:.0f}%", f"剩余额度 {quota:.0f}%", "OK")


def _format_balance(balance: float | None) -> tuple[str, str, str]:
    """格式化余额信息"""
    if balance is None:
        return ("UNKNOWN", "余额未知", "UNKNOWN")

    return (f"¥{balance:.2f}", f"余额 ¥{balance:.2f}", "OK")


def _format_cost(cost: float | None) -> tuple[str, str, str]:
    """格式化费用信息"""
    if cost is None:
        return ("UNKNOWN", "费用未知", "UNKNOWN")

    return (f"¥{cost:.2f}", f"今日费用 ¥{cost:.2f}", "OK")


def _format_activity(sessions: int, tool_calls: int, minutes: int) -> tuple[str, str, str]:
    """格式化活动信息"""
    value = f"{sessions} 会话 / {tool_calls} 调用"
    detail = f"活跃 {minutes} 分钟"
    status = "OK" if sessions > 0 or tool_calls > 0 else "IDLE"

    return (value, detail, status)


def aggregate_resources() -> dict[str, ResourceItem]:
    """
    聚合所有资源信息。

    Returns:
        聚合后的资源字典
    """
    state = state_manager.get_state()
    resources = {}

    # Codex 5H 额度 (包含 reset 时间)
    codex_5h_value, codex_5h_detail, codex_5h_status = _format_quota(state.resource.codex_percent)
    codex_5h_reset = state.resource.codex_reset_at
    if codex_5h_reset:
        codex_5h_detail = f"{codex_5h_reset}重置 剩余额度 {codex_5h_value}"
    resources["codex_5h"] = ResourceItem(
        title="Codex 5H",
        value=codex_5h_value,
        detail=codex_5h_detail,
        status=codex_5h_status,
    )

    # Codex 7D 额度 (包含 reset 日期)
    codex_7d_value, codex_7d_detail, codex_7d_status = _format_quota(state.resource.codex_weekly_percent)
    codex_7d_reset = state.resource.codex_weekly_reset_at
    if codex_7d_reset:
        codex_7d_detail = f"{codex_7d_reset}重置 剩余额度 {codex_7d_value}"
    resources["codex_7d"] = ResourceItem(
        title="Codex 7D",
        value=codex_7d_value,
        detail=codex_7d_detail,
        status=codex_7d_status,
    )

    # DeepSeek 余额 (v1.3.0: 检查 API Key 配置状态)
    try:
        from app.monitors.deepseek_balance_monitor import _get_api_key
        ds_api_key = _get_api_key()
        if not ds_api_key:
            resources["deepseek_balance"] = ResourceItem(
                title="DeepSeek 余额",
                value="—",
                detail="未配置 DEEPSEEK_API_KEY",
                status="NOT_CONFIGURED",
            )
        else:
            ds_balance_value, ds_balance_detail, ds_balance_status = _format_balance(state.resource.deepseek_balance)
            resources["deepseek_balance"] = ResourceItem(
                title="DeepSeek 余额",
                value=ds_balance_value,
                detail=ds_balance_detail,
                status=ds_balance_status,
            )
    except Exception:
        ds_balance_value, ds_balance_detail, ds_balance_status = _format_balance(state.resource.deepseek_balance)
        resources["deepseek_balance"] = ResourceItem(
            title="DeepSeek 余额",
            value=ds_balance_value,
            detail=ds_balance_detail,
            status=ds_balance_status,
        )

    # MiMo 余额 (v1.3.0: 检查 Cookie 配置状态)
    try:
        from app.monitors.mimo_balance_monitor import _get_cookie
        mimo_cookie = _get_cookie()
        if not mimo_cookie:
            resources["mimo_balance"] = ResourceItem(
                title="MiMo 余额",
                value="—",
                detail="未配置 MIMO_COOKIE",
                status="NOT_CONFIGURED",
            )
        else:
            mimo_value, mimo_detail, mimo_status = _format_balance(state.resource.mimo_balance)
            resources["mimo_balance"] = ResourceItem(
                title="MiMo 余额",
                value=mimo_value,
                detail=mimo_detail,
                status=mimo_status,
            )
    except Exception:
        mimo_value, mimo_detail, mimo_status = _format_balance(state.resource.mimo_balance)
        resources["mimo_balance"] = ResourceItem(
            title="MiMo 余额",
            value=mimo_value,
            detail=mimo_detail,
            status=mimo_status,
        )

    # AI 活动（从 agents 统计）
    sessions = sum(1 for a in state.agents.values() if a.status == "RUNNING")
    tool_calls = 0  # 需要从 events.jsonl 统计
    minutes = 0  # 需要从 events.jsonl 统计

    activity_value, activity_detail, activity_status = _format_activity(sessions, tool_calls, minutes)
    resources["ai_activity"] = ResourceItem(
        title="AI 活动",
        value=activity_value,
        detail=activity_detail,
        status=activity_status,
    )

    return resources


def get_resource_list() -> list[dict[str, Any]]:
    """
    获取资源列表。

    Returns:
        资源字典列表
    """
    resources = aggregate_resources()
    return [item.to_dict() for item in resources.values()]


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Dashboard Resources ===")
    print()

    resources = aggregate_resources()

    for key, item in resources.items():
        print(f"{item.title}:")
        print(f"  Value: {item.value}")
        print(f"  Detail: {item.detail}")
        print(f"  Status: {item.status}")
        print()


if __name__ == "__main__":
    main()
