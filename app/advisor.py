"""AI 建议生成器，根据工作状态自动生成建议。"""

from __future__ import annotations

from app.work_state import WorkState


def generate_suggestions(state: WorkState) -> list[str]:
    """根据工作状态生成建议列表。"""
    suggestions = []

    # 1. Agent 需要处理
    if state.agent_summary.needs_attention > 0:
        suggestions.append(f"有 {state.agent_summary.needs_attention} 个 Agent 需要处理")

    # 2. 当前项目状态
    if state.current_project.status == "需要授权":
        suggestions.append("当前项目需要授权，请及时处理")
    elif state.current_project.status == "运行异常":
        suggestions.append("当前项目运行异常，请检查")
    elif state.current_project.status == "运行中":
        # 检查是否超时
        if state.current_project.elapsed_minutes > state.current_project.target_minutes:
            suggestions.append("当前项目已超出目标时间")
        else:
            progress = state.current_project.elapsed_minutes / max(state.current_project.target_minutes, 1)
            if progress > 0.8:
                suggestions.append("当前项目即将完成")

    # 3. Codex 额度
    if state.ai_resource.codex_percent < 20:
        suggestions.append("Codex 额度不足，建议休息")
    elif state.ai_resource.codex_percent > 60:
        suggestions.append("Codex 额度充足，可接新项目")

    # 4. 余额提醒
    if state.ai_resource.deepseek_balance < 10:
        suggestions.append("DeepSeek 余额不足，请充值")
    if state.ai_resource.mimo_balance < 10:
        suggestions.append("MiMo 余额不足，请充值")

    # 5. 今日目标
    remaining = state.daily_goal.target - state.daily_goal.completed
    if remaining > 0:
        suggestions.append(f"今日还需完成 {remaining} 个项目")
    else:
        suggestions.append("今日目标已完成")

    # 6. 运行中的 Agent
    if state.agent_summary.running > 0:
        suggestions.append(f"有 {state.agent_summary.running} 个 Agent 正在运行")

    return suggestions[:5]  # 最多显示5条
