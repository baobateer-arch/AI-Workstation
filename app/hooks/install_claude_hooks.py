"""Claude Code Hooks 安装器 - 安全地配置 Claude Code Hooks。"""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Hook 标识符（用于识别本项目添加的 Hook）
HOOK_IDENTIFIER = "ai-workstation-dashboard"

# 旧版 Hook 标识符（用于识别需要升级的旧 Hook）
OLD_HOOK_IDENTIFIER = "-m app.hooks.claude_hook_handler"

# Hook handler 路径
HOOK_HANDLER_PATH = PROJECT_ROOT / "app" / "hooks" / "claude_hook_handler.py"

# 需要安装的 Hooks
REQUIRED_HOOKS = {
    "Notification": {
        "cli_arg": "notification",
        "description": "AI 工作站 - 处理通知事件",
    },
    "Stop": {
        "cli_arg": "stop",
        "description": "AI 工作站 - 处理停止事件",
    },
    "SessionStart": {
        "cli_arg": "session_start",
        "description": "AI 工作站 - 处理会话开始事件",
    },
    "PreToolUse": {
        "cli_arg": "pre_tool_use",
        "description": "AI 工作站 - 捕获工具执行前状态",
    },
}


def _build_command(cli_arg: str) -> str:
    """构建 Hook 命令"""
    return f'"{sys.executable}" "{HOOK_HANDLER_PATH}" {cli_arg}'


def find_claude_config_dir() -> Path | None:
    """
    查找 Claude Code 配置目录。

    搜索顺序（优先级从高到低）：
    1. ~/.claude/ (新版 Claude Code 首选)
    2. ~/AppData/Roaming/Claude/ (旧版 Windows)
    3. ~/Library/Application Support/Claude/ (macOS)
    4. ~/.config/claude/ (Linux)
    """
    home = Path.home()
    candidates = [
        home / ".claude",
        Path(os.environ.get("APPDATA", "")) / "Claude" if sys.platform == "win32" else None,
        home / "Library" / "Application Support" / "Claude" if sys.platform == "darwin" else None,
        home / ".config" / "claude" if sys.platform != "win32" else None,
    ]

    for path in candidates:
        if path and path.exists():
            return path

    return None


def find_settings_file(config_dir: Path | None = None) -> Path | None:
    """
    查找 Claude Code settings 文件。

    搜索顺序（优先级从高到低）：
    1. ~/.claude/settings.json
    2. ~/.claude/settings.local.json
    3. ~/AppData/Roaming/Claude/settings.json
    """
    home = Path.home()

    # 优先搜索路径
    search_paths = [
        home / ".claude" / "settings.json",
        home / ".claude" / "settings.local.json",
    ]

    # 添加 Windows 旧版路径
    appdata = os.environ.get("APPDATA")
    if appdata:
        search_paths.append(Path(appdata) / "Claude" / "settings.json")

    # 添加 macOS/Linux 路径
    if sys.platform == "darwin":
        search_paths.append(home / "Library" / "Application Support" / "Claude" / "settings.json")
    elif sys.platform != "win32":
        search_paths.append(home / ".config" / "claude" / "settings.json")

    for path in search_paths:
        if path.exists():
            return path

    # 如果指定了 config_dir，尝试在其中查找
    if config_dir:
        settings_file = config_dir / "settings.json"
        if settings_file.exists():
            return settings_file

    return None


def create_backup(settings_file: Path) -> Path:
    """创建备份"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = settings_file.parent / f"settings.json.backup.{timestamp}"
    shutil.copy2(settings_file, backup_file)
    return backup_file


def load_settings(settings_file: Path) -> dict[str, Any]:
    """加载设置"""
    try:
        with open(settings_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_settings(settings_file: Path, settings: dict[str, Any]) -> None:
    """保存设置"""
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def extract_hook_command(hook_value: Any) -> str | None:
    """
    从 Hook 值中提取命令字符串。

    支持两种格式：
    1. 新格式: {"matcher": "", "hooks": [{"type": "command", "command": "..."}]}
    2. 旧格式: {"command": "...", "description": "..."}
    """
    if isinstance(hook_value, dict):
        # 新格式：从 hooks 数组中提取
        hooks_array = hook_value.get("hooks", [])
        if isinstance(hooks_array, list) and hooks_array:
            first = hooks_array[0]
            if isinstance(first, dict):
                return first.get("command", "")
        # 旧格式：直接从 dict 提取
        return hook_value.get("command", "")
    elif isinstance(hook_value, list) and hook_value:
        first = hook_value[0]
        if isinstance(first, str):
            return first
        elif isinstance(first, dict):
            return extract_hook_command(first)
    elif isinstance(hook_value, str):
        return hook_value
    return None


def is_our_hook(hook_value: Any) -> bool:
    """检查是否是我们项目添加的 Hook（新格式或旧格式）"""
    cmd = extract_hook_command(hook_value)
    if cmd:
        # 新格式：包含绝对路径调用
        if HOOK_IDENTIFIER in cmd:
            return True
        # 旧格式：包含 -m app.hooks.claude_hook_handler
        if OLD_HOOK_IDENTIFIER in cmd:
            return True
    # 也检查 description（旧格式）
    if isinstance(hook_value, dict):
        desc = hook_value.get("description", "")
        if HOOK_IDENTIFIER in desc:
            return True
    return False


def is_old_format_hook(hook_value: Any) -> bool:
    """检查是否是旧格式的 Hook（需要升级）"""
    cmd = extract_hook_command(hook_value)
    if cmd and OLD_HOOK_IDENTIFIER in cmd:
        return True
    return False


def find_old_hooks(hooks: dict[str, Any]) -> dict[str, list]:
    """查找所有旧格式的 Hook"""
    old_hooks = {}
    for event_name, hook_value in hooks.items():
        if isinstance(hook_value, list):
            old_in_list = [h for h in hook_value if is_old_format_hook(h)]
            if old_in_list:
                old_hooks[event_name] = old_in_list
        elif is_old_format_hook(hook_value):
            old_hooks[event_name] = [hook_value]
    return old_hooks


def install_hooks(settings_file: Path, dry_run: bool = False) -> dict[str, Any]:
    """
    安装 Hooks。

    Args:
        settings_file: settings.json 路径
        dry_run: 是否为 dry-run 模式

    Returns:
        安装结果
    """
    settings = load_settings(settings_file)
    hooks = settings.get("hooks", {})

    result = {
        "settings_file": str(settings_file),
        "dry_run": dry_run,
        "backup_file": None,
        "installed": [],
        "skipped": [],
        "removed_old": [],
        "upgraded": [],
    }

    if not dry_run:
        # 创建备份
        backup = create_backup(settings_file)
        result["backup_file"] = str(backup)

    # 安装每个 Hook
    for event_name, hook_config in REQUIRED_HOOKS.items():
        existing = hooks.get(event_name)

        # 检查是否已存在旧格式的 Hook
        if existing:
            has_old = False
            has_new = False

            if isinstance(existing, list):
                has_old = any(is_old_format_hook(h) for h in existing)
                has_new = any(is_our_hook(h) and not is_old_format_hook(h) for h in existing)
            elif isinstance(existing, dict):
                has_old = is_old_format_hook(existing)
                has_new = is_our_hook(existing) and not is_old_format_hook(existing)

            # 如果有旧格式，需要删除并替换
            if has_old:
                result["removed_old"].append(event_name)
                # 如果是列表，过滤掉旧格式；如果是单个对象，删除整个
                if isinstance(existing, list):
                    hooks[event_name] = [h for h in existing if not is_old_format_hook(h)]
                else:
                    del hooks[event_name]
                existing = hooks.get(event_name)

            # 如果已有新格式，跳过
            if has_new and not has_old:
                result["skipped"].append(event_name)
                continue

        # 构建新 Hook 条目（Claude Code 新格式）
        command = _build_command(hook_config["cli_arg"])
        new_hook = {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                }
            ],
        }

        # 合并到现有 Hooks
        if event_name not in hooks:
            hooks[event_name] = [new_hook]
        elif isinstance(hooks[event_name], list):
            hooks[event_name].append(new_hook)
        else:
            # 转换为列表
            hooks[event_name] = [hooks[event_name], new_hook]

        if event_name in result.get("removed_old", []):
            result["upgraded"].append(event_name)
        else:
            result["installed"].append(event_name)

    # 更新 settings
    settings["hooks"] = hooks

    if not dry_run:
        save_settings(settings_file, settings)

    return result


def uninstall_hooks(settings_file: Path, dry_run: bool = False) -> dict[str, Any]:
    """
    卸载本项目添加的 Hooks。

    Args:
        settings_file: settings.json 路径
        dry_run: 是否为 dry-run 模式

    Returns:
        卸载结果
    """
    settings = load_settings(settings_file)
    hooks = settings.get("hooks", {})

    result = {
        "settings_file": str(settings_file),
        "dry_run": dry_run,
        "backup_file": None,
        "removed": [],
        "kept": [],
    }

    if not dry_run:
        # 创建备份
        backup = create_backup(settings_file)
        result["backup_file"] = str(backup)

    # 移除每个 Hook
    for event_name in REQUIRED_HOOKS.keys():
        existing = hooks.get(event_name)
        if not existing:
            continue

        if isinstance(existing, list):
            # 过滤掉我们的 Hook
            filtered = [h for h in existing if not is_our_hook(h)]
            if len(filtered) < len(existing):
                result["removed"].append(event_name)
                if filtered:
                    hooks[event_name] = filtered
                else:
                    del hooks[event_name]
            else:
                result["kept"].append(event_name)
        elif is_our_hook(existing):
            result["removed"].append(event_name)
            del hooks[event_name]
        else:
            result["kept"].append(event_name)

    # 更新 settings
    settings["hooks"] = hooks

    if not dry_run:
        save_settings(settings_file, settings)

    return result


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def _get_hook_handler_path() -> str:
    """获取 Hook handler 的绝对路径"""
    handler = PROJECT_ROOT / "app" / "hooks" / "claude_hook_handler.py"
    return str(handler)


def _get_python_path() -> str:
    """获取 Python 解释器的绝对路径"""
    return sys.executable


def _event_name_to_cli(event_name: str) -> str:
    """将事件名转换为 CLI 参数格式"""
    mapping = {
        "Notification": "notification",
        "Stop": "stop",
        "SessionStart": "session_start",
        "PreToolUse": "pre_tool_use",
    }
    return mapping.get(event_name, event_name.lower())


def _build_hook_json(event_name: str, description: str) -> dict[str, Any]:
    """构建单个 Hook 的 JSON 片段（Claude Code 新格式）"""
    cli_arg = _event_name_to_cli(event_name)
    command = _build_command(cli_arg)

    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
        "_description": description,
    }


def _print_dry_run_verbose(settings_file: Path) -> None:
    """打印详细的 dry-run 信息"""
    settings = load_settings(settings_file)
    hooks = settings.get("hooks", {})

    # 检测旧 Hook
    old_hooks = find_old_hooks(hooks)

    print()
    print("=" * 60)
    print("  Claude Code Hooks 安装预览 (详细模式)")
    print("=" * 60)

    # 1. 配置文件信息
    print()
    print("[1/5] 配置文件:")
    print(f"      {settings_file}")

    # 2. 检测旧 Hook
    print()
    print("[2/5] 检测旧 Hook:")
    if old_hooks:
        for event_name, hook_list in old_hooks.items():
            print(f"      {event_name}: 旧格式")
            for h in hook_list:
                cmd = extract_hook_command(h) or "N/A"
                print(f"        - {cmd[:70]}...")
    else:
        print("      未发现旧格式 Hook")

    # 3. 当前已有的 hooks（新格式）
    print()
    print("[3/5] 当前已有 hooks:")
    has_any = False
    for event_name, hook_value in hooks.items():
        if event_name in old_hooks:
            continue  # 跳过旧格式
        if isinstance(hook_value, list):
            new_hooks = [h for h in hook_value if not is_old_format_hook(h)]
            if new_hooks:
                has_any = True
                print(f"      {event_name}: {len(new_hooks)} 个")
                for i, h in enumerate(new_hooks):
                    cmd = extract_hook_command(h) or "N/A"
                    print(f"        [{i+1}] {cmd[:70]}...")
        elif not is_old_format_hook(hook_value):
            has_any = True
            cmd = extract_hook_command(hook_value) or "N/A"
            print(f"      {event_name}: {cmd[:70]}...")
    if not has_any:
        print("      None")

    # 4. 计划操作
    print()
    print("[4/5] 计划操作:")
    to_remove_old = list(old_hooks.keys())
    to_install = []
    to_skip = []

    for event_name in REQUIRED_HOOKS.keys():
        existing = hooks.get(event_name)
        if event_name in old_hooks:
            # 旧 Hook 将被替换
            to_install.append(event_name)
        elif existing:
            if isinstance(existing, list):
                has_new = any(is_our_hook(h) and not is_old_format_hook(h) for h in existing)
            else:
                has_new = is_our_hook(existing) and not is_old_format_hook(existing)
            if has_new:
                to_skip.append(event_name)
            else:
                to_install.append(event_name)
        else:
            to_install.append(event_name)

    if to_remove_old:
        print(f"      删除旧 Hook: {', '.join(to_remove_old)}")
    if to_install:
        print(f"      新增新 Hook: {', '.join(to_install)}")
    if to_skip:
        print(f"      跳过: {', '.join(to_skip)} (已是最新)")
    if not to_remove_old and not to_install and not to_skip:
        print("      无需变更")

    # 5. 新 Hook 格式
    print()
    print("[5/5] 新 Hook 格式 (Claude Code 新格式):")
    for event_name, hook_config in REQUIRED_HOOKS.items():
        hook_json = _build_hook_json(event_name, hook_config["description"])
        cmd = hook_json["hooks"][0]["command"]
        print(f"      {event_name}:")
        print(f"        matcher: \"\"")
        print(f"        hooks[0].type: command")
        print(f"        hooks[0].command: {cmd}")

    print()
    print("=" * 60)
    print("  不会修改任何文件")
    print("=" * 60)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python -m app.hooks.install_claude_hooks <command>")
        print()
        print("命令:")
        print("  install            安装 Hooks")
        print("  uninstall          卸载本项目 Hooks")
        print("  status             查看当前状态")
        print()
        print("选项:")
        print("  --dry-run          只显示计划，不写文件")
        print("  --verbose          详细输出（配合 --dry-run 使用）")
        sys.exit(1)

    cmd = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv

    # 查找配置文件（直接搜索 settings 文件）
    settings_file = find_settings_file()
    if not settings_file:
        # 尝试通过配置目录查找
        config_dir = find_claude_config_dir()
        if config_dir:
            settings_file = find_settings_file(config_dir)

    if not settings_file:
        print("[ERROR] 未找到 Claude Code 配置文件")
        print("        搜索路径:")
        print(f"          1. {Path.home() / '.claude' / 'settings.json'}")
        print(f"          2. {Path.home() / '.claude' / 'settings.local.json'}")
        appdata = os.environ.get("APPDATA")
        if appdata:
            print(f"          3. {Path(appdata) / 'Claude' / 'settings.json'}")
        print()
        print("        请确认 Claude Code 已安装并至少运行过一次")
        sys.exit(1)

    if not verbose:
        print(f"[INFO] Claude Code 配置:")
        print(f"       {settings_file}")

    if cmd == "install":
        if dry_run:
            if verbose:
                _print_dry_run_verbose(settings_file)
            else:
                print()
                print("[DRY RUN]")
                print()
                print("将增加:")
                for event_name in REQUIRED_HOOKS.keys():
                    print(f"  hooks.{event_name}")
                print()
                print("不会修改文件。")
        else:
            result = install_hooks(settings_file, dry_run=False)
            print()
            print("=== 安装结果 ===")
            if result["backup_file"]:
                print(f"备份文件: {result['backup_file']}")
            if result.get("removed_old"):
                print(f"已删除旧 Hook: {result['removed_old']}")
            if result.get("upgraded"):
                print(f"已升级: {result['upgraded']}")
            if result["installed"]:
                print(f"已安装: {result['installed']}")
            if result["skipped"]:
                print(f"已跳过: {result['skipped']}")

    elif cmd == "uninstall":
        if dry_run:
            print()
            print("[DRY RUN]")
            print()
            print("将移除:")
            for event_name in REQUIRED_HOOKS.keys():
                print(f"  hooks.{event_name}")
            print()
            print("不会修改文件。")
        else:
            result = uninstall_hooks(settings_file, dry_run=False)
            print()
            print("=== 卸载结果 ===")
            if result["backup_file"]:
                print(f"备份文件: {result['backup_file']}")
            print(f"已移除: {result['removed']}")
            print(f"已保留: {result['kept']}")

    elif cmd == "status":
        settings = load_settings(settings_file)
        hooks = settings.get("hooks", {})

        print()
        print("=== 当前 Hook 状态 ===")
        for event_name in REQUIRED_HOOKS.keys():
            existing = hooks.get(event_name)
            if existing:
                if isinstance(existing, list):
                    has_our = any(is_our_hook(h) for h in existing)
                    print(f"{event_name}: {len(existing)} 个 Hook (本项目: {'是' if has_our else '否'})")
                else:
                    has_our = is_our_hook(existing)
                    print(f"{event_name}: 1 个 Hook (本项目: {'是' if has_our else '否'})")
            else:
                print(f"{event_name}: 无")

    else:
        print(f"[ERROR] 未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
