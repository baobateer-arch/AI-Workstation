"""Agent 状态定义。"""

from __future__ import annotations


# 状态常量
STATUS_IDLE = "idle"
STATUS_RUNNING = "running"
STATUS_WAITING_INPUT = "waiting_input"
STATUS_WAITING_AUTH = "waiting_auth"
STATUS_ERROR = "error"
STATUS_COMPLETED = "completed"

# 状态中文显示
STATUS_CN = {
    STATUS_IDLE: "空闲",
    STATUS_RUNNING: "运行中",
    STATUS_WAITING_INPUT: "等待输入",
    STATUS_WAITING_AUTH: "等待授权",
    STATUS_ERROR: "错误",
    STATUS_COMPLETED: "完成",
}

# 需要处理的状态
NEEDS_ATTENTION = {STATUS_WAITING_INPUT, STATUS_WAITING_AUTH, STATUS_ERROR}

# 优先级（数值越小越优先）
PRIORITY = {
    STATUS_WAITING_AUTH: 0,
    STATUS_WAITING_INPUT: 1,
    STATUS_ERROR: 2,
    STATUS_COMPLETED: 3,
    STATUS_RUNNING: 4,
    STATUS_IDLE: 5,
}


def needs_attention(status: str) -> bool:
    """判断是否需要处理"""
    return status in NEEDS_ATTENTION


def get_priority(status: str) -> int:
    return PRIORITY.get(status, 99)


def status_cn(status: str) -> str:
    return STATUS_CN.get(status, status)
