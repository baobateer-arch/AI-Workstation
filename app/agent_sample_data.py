"""Static sample data for agent status board (v0.3)."""

AGENT_SAMPLE_DATA = {
    "generated_at": "2026-07-11T20:44:00+08:00",
    "agents": [
        {
            "id": "codex",
            "name": "Codex",
            "status": "running",
            "project": "客户管理系统",
            "task": "实现用户登录模块",
            "message": "正在编写和测试代码",
            "started_at": "2026-07-11T20:20:00+08:00",
            "waiting_since": None,
            "needs_attention": False,
        },
        {
            "id": "claude_code",
            "name": "Claude Code",
            "status": "permission_required",
            "project": "前端管理后台",
            "task": "安装项目依赖",
            "message": "请求执行：npm install",
            "started_at": "2026-07-11T20:16:00+08:00",
            "waiting_since": "2026-07-11T20:42:00+08:00",
            "needs_attention": True,
        },
        {
            "id": "mimo_code",
            "name": "MiMo Code",
            "status": "completed",
            "project": "Kindle AI 工作站",
            "task": "生成 Agent 值守台",
            "message": "代码生成完成，等待检查",
            "started_at": "2026-07-11T20:10:00+08:00",
            "waiting_since": "2026-07-11T20:43:00+08:00",
            "needs_attention": True,
        },
    ],
}
