"""常量定义 - 统一状态枚举。"""


class AgentStatus:
    """Agent 状态常量（统一大写格式）"""
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    STOPPED = "STOPPED"
    WAITING = "WAITING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PERMISSION = "PERMISSION"
    DONE = "DONE"
    ERROR = "ERROR"

    # 需要关注的状态
    ATTENTION_STATUSES = {PERMISSION, WAITING, WAITING_APPROVAL, ERROR}

    @classmethod
    def needs_attention(cls, status: str) -> bool:
        """检查状态是否需要关注"""
        return status.upper() in cls.ATTENTION_STATUSES

    @classmethod
    def normalize(cls, status: str) -> str:
        """标准化状态为大写"""
        return status.upper() if status else cls.IDLE
