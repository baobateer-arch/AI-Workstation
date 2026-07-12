# 数据结构定义

## WorkState

```python
{
    "generated_at": "ISO 时间戳",
    "status": "NORMAL | WARNING | STOP",
    "status_text": "可以继续工作 | 需要处理Agent | 需要立即处理",
    "daily_goal": {
        "completed": 2,
        "target": 5,
        "expected_income": 850.00,
        "avg_minutes": 45
    },
    "current_project": {
        "name": "项目名称",
        "elapsed_minutes": 47,
        "target_minutes": 60,
        "ai_cost": 1.62,
        "status": "运行中"
    },
    "ai_resource": {
        "codex_percent": 68,
        "codex_reset": "02:35",
        "deepseek_balance": 83.26,
        "mimo_balance": 46.20
    },
    "agent_summary": {
        "running": 2,
        "needs_attention": 1,
        "error_agents": []
    },
    "today_income": 1250.00,
    "suggestions": ["建议1", "建议2"]
}
```

## 状态规则

- NORMAL: 无异常
- WARNING: agent_summary.needs_attention > 0
- STOP: codex_percent < 20 或 deepseek_balance < 10 或 mimo_balance < 10
