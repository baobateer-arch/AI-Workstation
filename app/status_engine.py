"""状态计算引擎 - 判断当前工作状态。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# 状态常量
STATUS_NORMAL = "NORMAL"
STATUS_WARNING = "WARNING"
STATUS_STOP = "STOP"

# 状态中文
STATUS_TEXT = {
    STATUS_NORMAL: "可以继续工作",
    STATUS_WARNING: "需要处理Agent",
    STATUS_STOP: "需要立即处理",
}

# 状态符号
STATUS_SYMBOL = {
    STATUS_NORMAL: "✓",
    STATUS_WARNING: "⚠",
    STATUS_STOP: "✗",
}


@dataclass
class StatusResult:
    """状态计算结果"""
    status: str
    status_text: str
    symbol: str
    reasons: list[str]

    @property
    def is_normal(self) -> bool:
        return self.status == STATUS_NORMAL

    @property
    def is_warning(self) -> bool:
        return self.status == STATUS_WARNING

    @property
    def is_stop(self) -> bool:
        return self.status == STATUS_STOP


def calculate_status(
    codex_percent: float = 100,
    deepseek_balance: float = 100,
    mimo_balance: float = 100,
    agent_needs_attention: int = 0,
    agent_errors: list[str] | None = None,
) -> StatusResult:
    """
    计算当前工作状态。

    规则：
    - STOP: Codex < 20% 或余额不足 (<10)
    - WARNING: 存在 Agent 需要处理
    - NORMAL: 其他情况
    """
    reasons = []

    # 检查 STOP 条件
    if codex_percent < 20:
        reasons.append(f"Codex 额度不足 ({codex_percent:.0f}%)")
    if deepseek_balance < 10:
        reasons.append(f"DeepSeek 余额不足 (¥{deepseek_balance:.2f})")
    if mimo_balance < 10:
        reasons.append(f"MiMo 余额不足 (¥{mimo_balance:.2f})")
    if agent_errors:
        for err in agent_errors:
            reasons.append(f"Agent 异常: {err}")

    if reasons:
        return StatusResult(
            status=STATUS_STOP,
            status_text=STATUS_TEXT[STATUS_STOP],
            symbol=STATUS_SYMBOL[STATUS_STOP],
            reasons=reasons,
        )

    # 检查 WARNING 条件
    if agent_needs_attention > 0:
        reasons.append(f"有 {agent_needs_attention} 个 Agent 需要处理")
        return StatusResult(
            status=STATUS_WARNING,
            status_text=STATUS_TEXT[STATUS_WARNING],
            symbol=STATUS_SYMBOL[STATUS_WARNING],
            reasons=reasons,
        )

    # NORMAL
    return StatusResult(
        status=STATUS_NORMAL,
        status_text=STATUS_TEXT[STATUS_NORMAL],
        symbol=STATUS_SYMBOL[STATUS_NORMAL],
        reasons=[],
    )


def calculate_status_from_dict(data: dict[str, Any]) -> StatusResult:
    """从字典数据计算状态。"""
    resource = data.get("ai_resource", {})
    agent = data.get("agent_summary", {})

    return calculate_status(
        codex_percent=float(resource.get("codex_percent", 100)),
        deepseek_balance=float(resource.get("deepseek_balance", 100)),
        mimo_balance=float(resource.get("mimo_balance", 100)),
        agent_needs_attention=int(agent.get("needs_attention", 0)),
        agent_errors=agent.get("error_agents"),
    )
