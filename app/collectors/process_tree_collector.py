"""进程树检测器 - 检测 VS Code 和 Claude 进程树。"""

from __future__ import annotations

import subprocess
import sys
from typing import Any


def get_process_tree() -> list[dict[str, Any]]:
    """
    获取进程树信息。

    Returns:
        list: 进程列表，包含 PID、名称、父 PID
    """
    try:
        if sys.platform == "win32":
            # Windows: 使用 wmic 获取进程树
            result = subprocess.run(
                ["wmic", "process", "get", "ProcessId,Name,ParentProcessId", "/FORMAT:CSV"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            processes = []
            for line in lines[1:]:  # 跳过标题
                parts = line.strip().split(",")
                if len(parts) >= 4:
                    try:
                        processes.append({
                            "name": parts[1],
                            "pid": int(parts[3]),
                            "parent_pid": int(parts[2]),
                        })
                    except (ValueError, IndexError):
                        continue
            return processes
        else:
            # Linux/Mac: 使用 ps
            result = subprocess.run(
                ["ps", "-eo", "pid,ppid,comm"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = result.stdout.strip().split("\n")[1:]
            processes = []
            for line in lines:
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    processes.append({
                        "name": parts[2],
                        "pid": int(parts[0]),
                        "parent_pid": int(parts[1]),
                    })
            return processes
    except Exception:
        return []


def find_process_by_name(name: str) -> list[dict[str, Any]]:
    """按名称查找进程"""
    all_procs = get_process_tree()
    return [p for p in all_procs if name.lower() in p["name"].lower()]


def get_children(pid: int) -> list[dict[str, Any]]:
    """获取进程的子进程"""
    all_procs = get_process_tree()
    return [p for p in all_procs if p["parent_pid"] == pid]


def get_process_tree_by_root(root_name: str) -> dict[str, Any]:
    """
    获取以指定进程为根的进程树。

    Args:
        root_name: 根进程名称（如 Code.exe）

    Returns:
        dict: 包含根进程和子进程树
    """
    roots = find_process_by_name(root_name)
    all_procs = get_process_tree()

    trees = []
    for root in roots:
        tree = {
            "root": root,
            "children": [],
        }

        # 递归查找子进程
        def find_children(parent_pid, depth=0):
            if depth > 10:  # 防止无限递归
                return
            for proc in all_procs:
                if proc["parent_pid"] == parent_pid:
                    tree["children"].append(proc)
                    find_children(proc["pid"], depth + 1)

        find_children(root["pid"])
        trees.append(tree)

    return {"trees": trees, "total": len(trees)}


def detect_vscode_claude_tree() -> dict[str, Any]:
    """
    检测 VS Code 和 Claude 进程树。

    Returns:
        dict: 检测结果
    """
    # 查找 VS Code
    vscode_procs = find_process_by_name("Code.exe")
    vscode_running = len(vscode_procs) > 0

    # 查找 Claude 相关进程
    claude_names = ["claude", "Claude"]
    claude_procs = []
    for name in claude_names:
        claude_procs.extend(find_process_by_name(name))

    claude_running = len(claude_procs) > 0

    # 查找 node 进程（Claude 可能通过 node 运行）
    node_procs = find_process_by_name("node.exe")

    # 构建进程树信息
    vscode_tree = get_process_tree_by_root("Code.exe") if vscode_running else None

    return {
        "vscode_running": vscode_running,
        "vscode_count": len(vscode_procs),
        "claude_running": claude_running,
        "claude_count": len(claude_procs),
        "node_running": len(node_procs) > 0,
        "node_count": len(node_procs),
        "vscode_tree": vscode_tree,
        "claude_procs": claude_procs[:5],  # 只返回前5个
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== 进程树检测 ===")
    result = detect_vscode_claude_tree()
    print(f"VS Code 运行: {result['vscode_running']} ({result['vscode_count']})")
    print(f"Claude 运行: {result['claude_running']} ({result['claude_count']})")
    print(f"Node 运行: {result['node_running']} ({result['node_count']})")

    if result["claude_procs"]:
        print("\nClaude 进程:")
        for p in result["claude_procs"]:
            print(f"  - {p['name']} (PID: {p['pid']})")


if __name__ == "__main__":
    main()
