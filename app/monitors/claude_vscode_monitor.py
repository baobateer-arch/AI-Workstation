"""Claude Code VS Code 监听器框架。"""

from __future__ import annotations

import sys
from typing import Any

from app.agent_runtime import update_agent_status, clear_agent_status, get_agent_status
from app.collectors.process_collector import detect_processes
from app.collectors.process_tree_collector import detect_vscode_claude_tree


# Agent 标识符
AGENT_ID = "claude_code_vscode"

# 支持的状态
STATUSES = {
    "running": "RUNNING",
    "permission": "PERMISSION",
    "waiting": "WAITING",
    "done": "DONE",
    "error": "ERROR",
}


def simulate_status(
    status: str,
    message: str = "",
    project: str = "",
) -> dict[str, Any]:
    """
    模拟 Claude Code 状态变化。

    Args:
        status: 状态（running/permission/waiting/done/error）
        message: 状态消息
        project: 当前项目

    Returns:
        更新后的状态字典
    """
    mapped_status = STATUSES.get(status.lower(), "RUNNING")
    return update_agent_status(
        agent_id=AGENT_ID,
        status=mapped_status,
        message=message,
        project=project,
    )


def clear_status() -> bool:
    """清除 Claude Code 状态"""
    return clear_agent_status(AGENT_ID)


def get_status() -> dict[str, Any] | None:
    """获取当前状态"""
    return get_agent_status(AGENT_ID)


def detect_process_tree() -> dict[str, Any]:
    """
    检测 VS Code 和 Claude 进程树。

    Returns:
        dict: 进程树检测结果
    """
    return detect_vscode_claude_tree()


def auto_detect() -> dict[str, Any]:
    """
    自动检测 Claude Code 状态。

    逻辑：
    - 使用进程树检测 VS Code 和 Claude
    - 如果检测到 Claude 进程运行 -> 更新为 RUNNING
    - 如果没有检测到 -> 保持原状态

    Returns:
        dict: 检测结果和状态更新信息
    """
    # 使用进程树检测
    tree_result = detect_process_tree()
    claude_running = tree_result.get("claude_running", False)
    vscode_running = tree_result.get("vscode_running", False)

    # 获取当前状态
    current = get_agent_status(AGENT_ID)
    current_status = current.get("status") if current else None

    result = {
        "claude_running": claude_running,
        "vscode_running": vscode_running,
        "previous_status": current_status,
        "updated": False,
        "new_status": current_status,
        "detection_method": "process_tree",
    }

    if claude_running and current_status != "RUNNING":
        # Claude 正在运行，更新状态
        update_agent_status(
            agent_id=AGENT_ID,
            status="RUNNING",
            message="进程树检测：Claude 正在运行",
        )
        result["updated"] = True
        result["new_status"] = "RUNNING"
    elif not claude_running and current_status == "RUNNING":
        # Claude 未运行，但当前状态是 RUNNING -> 更新为 IDLE
        update_agent_status(
            agent_id=AGENT_ID,
            status="IDLE",
            message="进程树检测：Claude 未运行",
        )
        result["updated"] = True
        result["new_status"] = "IDLE"
    # 其他情况保持原状态

    return result


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python -m app.monitors.claude_vscode_monitor <command> [args...]")
        print()
        print("命令:")
        print("  auto               自动检测 Claude 状态")
        print("  tree               检测进程树")
        print("  running [msg]      设置为运行中")
        print("  permission [msg]   设置为等待授权")
        print("  waiting [msg]      设置为等待输入")
        print("  done [msg]         设置为完成")
        print("  error [msg]        设置为错误")
        print("  status             查看当前状态")
        print("  clear              清除状态")
        print()
        print("示例:")
        print("  python -m app.monitors.claude_vscode_monitor auto")
        print("  python -m app.monitors.claude_vscode_monitor tree")
        print("  python -m app.monitors.claude_vscode_monitor permission \"npm install\"")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "auto":
        result = auto_detect()
        print(f"[OK] 自动检测结果:")
        print(f"     Claude 运行: {result['claude_running']}")
        print(f"     VS Code 运行: {result['vscode_running']}")
        print(f"     之前状态: {result['previous_status']}")
        print(f"     已更新: {result['updated']}")
        print(f"     当前状态: {result['new_status']}")

    elif cmd == "tree":
        result = detect_process_tree()
        print(f"[OK] 进程树检测:")
        print(f"     VS Code: {result['vscode_running']} ({result['vscode_count']})")
        print(f"     Claude: {result['claude_running']} ({result['claude_count']})")
        print(f"     Node: {result['node_running']} ({result['node_count']})")
        if result.get("claude_procs"):
            print("     Claude 进程:")
            for p in result["claude_procs"][:3]:
                print(f"       - {p['name']} (PID: {p['pid']})")

    elif cmd == "status":
        status = get_status()
        if status:
            print(f"[OK] 当前状态: {status}")
        else:
            print("[INFO] 无状态记录")

    elif cmd == "clear":
        clear_status()
        print("[OK] 状态已清除")

    else:
        # 设置状态
        message = sys.argv[2] if len(sys.argv) > 2 else ""
        project = sys.argv[3] if len(sys.argv) > 3 else ""
        result = simulate_status(cmd, message, project)
        print(f"[OK] 状态已更新: {result}")


if __name__ == "__main__":
    main()
