"""v0.5 测试数据。"""

V05_SAMPLE_DATA = {
    "generated_at": "2026-07-11T21:20:00+08:00",
    "daily_goal": {
        "completed": 2,
        "target": 5,
        "expected_income": 850.00,
        "avg_minutes": 45,
    },
    "current_project": {
        "name": "客户管理系统",
        "elapsed_minutes": 47,
        "target_minutes": 60,
        "ai_cost": 1.62,
        "status": "运行中",
    },
    "ai_resource": {
        "codex_percent": 68,
        "codex_reset": "02:35",
        "deepseek_balance": 83.26,
        "mimo_balance": 46.20,
    },
    "agent_summary": {
        "running": 2,
        "needs_attention": 1,
        "attention_agents": ["Claude Code"],
        "error_agents": [],
    },
    "suggestions": [
        "先处理 Claude Code 授权",
        "然后继续当前项目",
    ],
    "today_income": 1250.00,
}
