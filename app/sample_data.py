"""Static sample data for v0.1 dashboard rendering."""

SAMPLE_DATA = {
    "codex": {
        "five_hour_percent": 68,
        "weekly_percent": 41,
        "reset_text": "02:35",
    },
    "deepseek": {
        "balance": {"total": 83.26},
        "usage": {
            "today": {
                "total_tokens": 1_820_000,
                "prompt_tokens": 1_310_000,
                "completion_tokens": 510_000,
                "cost": 2.43,
            }
        },
    },
    "mimo": {
        "balance": {"total": 46.20},
        "usage": {
            "today": {
                "total_tokens": 3_460_000,
                "prompt_tokens": 2_810_000,
                "completion_tokens": 650_000,
                "cost": 3.17,
            }
        },
    },
    "current_project": {
        "name": "客户管理系统",
        "elapsed_minutes": 47,
        "target_minutes": 60,
        "total_cost": 1.62,
        "income_today": 0,
    },
    "status": "ALL ONLINE",
    "version": "v0.1",
}
