"""Agent 健康检测器 - 统一检测 Agent 真实状态。

v1.5.0: 修正状态优先级，修复 IDLE 无法出现的问题。
  优先级：
  1. STOPPED — 进程不存在
  2. WAITING_APPROVAL — 存在未完成授权请求
  3. RUNNING — 存在近期任务活动
  4. IDLE — 进程存在，但没有任务活动
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.constants import AgentStatus


# 数据目录
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
EVENTS_FILE = DATA_DIR / "events.jsonl"

# Claude 数据目录
CLAUDE_HOME = Path.home() / ".claude"
CLAUDE_SESSIONS_DIR = CLAUDE_HOME / "sessions"
CLAUDE_PROJECTS_DIR = CLAUDE_HOME / "projects"

# Codex 数据目录
CODEX_HOME = Path.home() / ".codex"
CODEX_SESSIONS_DIR = CODEX_HOME / "sessions"
CODEX_CHAT_PROCESSES = CODEX_HOME / "process_manager" / "chat_processes.json"

# 活跃超时（5分钟）
ACTIVE_TIMEOUT_SECONDS = 5 * 60

# 进程名模式
PROCESS_CLAUDE = ["claude.exe", "Claude.exe"]
PROCESS_CODEX = ["codex.exe", "Codex.exe"]
PROCESS_MIMO = ["mimo.exe", "MiMo.exe"]
# MiMo Code runtime data (the cron lock only indicates that the service is alive)
MIMO_DATA_DIR = Path.home() / ".local" / "share" / "mimocode"
MIMO_DB_FILE = MIMO_DATA_DIR / "mimocode.db"
MIMO_LOG_DIR = MIMO_DATA_DIR / "log"

_MIMO_PERMISSION_ASK_RE = re.compile(
    r"\bservice=permission\b.*?\bid=([^\s]+)\b.*?"
    r"\bpermission=([^\s]+)\b.*?\basking\b"
)
_MIMO_PERMISSION_REPLY_RE = re.compile(r"/permission/([^/\s]+)/reply\b")
_MIMO_PERMISSION_LOG_CACHE: dict[str, dict[str, Any]] = {}


def _tasklist() -> str:
    """获取 Windows 进程列表（小写）"""
    try:
        if sys.platform != "win32":
            return ""
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.lower()
    except Exception:
        return ""


def _process_exists(process_list: str, patterns: list[str]) -> bool:
    """检查进程是否存在于 tasklist 输出中"""
    for pattern in patterns:
        if pattern.lower() in process_list:
            return True
    return False


def _format_last_activity(dt: datetime | None) -> str:
    """将 datetime 格式化为相对时间字符串。

    格式示例:
      - "just now"
      - "30 sec ago"
      - "5 min ago"
      - "2 hours ago"
      - "" (无数据)
    """
    if dt is None:
        return ""

    elapsed = (datetime.now() - dt).total_seconds()

    if elapsed < 0:
        return "just now"
    if elapsed < 60:
        return "just now"
    if elapsed < 3600:
        minutes = int(elapsed // 60)
        return f"{minutes} min ago"
    if elapsed < 86400:
        hours = int(elapsed // 3600)
        return f"{hours} hours ago"
    days = int(elapsed // 86400)
    return f"{days} days ago"


def _get_last_claude_event_time() -> datetime | None:
    """从 Claude session JSONL 获取最近的活动时间。

    读取活跃会话的 JSONL 文件，查找最后的 assistant 消息时间。

    Returns:
        最近活动时间，无活动返回 None
    """
    session = _get_active_claude_session()
    if not session:
        return None

    session_id = session.get("sessionId")
    if not session_id:
        return None

    jsonl_path = _find_claude_session_jsonl(session_id)
    if not jsonl_path:
        return None

    events = _read_jsonl_tail(jsonl_path)
    if not events:
        return None

    # 从后往前找最后的 assistant 消息
    for evt in reversed(events):
        if evt.get("type") == "assistant":
            ts_str = evt.get("timestamp")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    return ts.replace(tzinfo=None)
                except (ValueError, TypeError):
                    pass
            break

    return None


def _is_recently_active(timeout_seconds: int = ACTIVE_TIMEOUT_SECONDS) -> bool:
    """检查 Claude 是否在最近 timeout_seconds 内有活跃事件。

    Returns:
        True 如果有近期活跃事件
    """
    last_event_time = _get_last_claude_event_time()
    if last_event_time is None:
        return False

    elapsed = (datetime.now() - last_event_time).total_seconds()
    return elapsed <= timeout_seconds


def _get_active_claude_session() -> dict[str, Any] | None:
    """获取当前活跃的 Claude 会话信息。

    从 ~/.claude/sessions/<pid>.json 读取活跃会话注册表。

    Returns:
        dict: {pid, sessionId, cwd, startedAt, ...} 或 None
    """
    if not CLAUDE_SESSIONS_DIR.exists():
        return None

    latest_session = None
    latest_mtime = 0

    for session_file in CLAUDE_SESSIONS_DIR.glob("*.json"):
        try:
            mtime = session_file.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
                with open(session_file, "r", encoding="utf-8") as f:
                    latest_session = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

    return latest_session


def _read_jsonl_tail(file_path: Path, tail_bytes: int = 16384) -> list[dict]:
    """读取 JSONL 文件尾部，返回最近的事件列表。"""
    if not file_path.exists():
        return []

    try:
        size = file_path.stat().st_size
        read_size = min(tail_bytes, size)

        with open(file_path, "rb") as f:
            if size > read_size:
                f.seek(size - read_size)
            raw = f.read().decode("utf-8", errors="replace")

        events = []
        for line in raw.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events
    except OSError:
        return []


def _find_claude_session_jsonl(session_id: str) -> Path | None:
    """根据 sessionId 查找对应的 JSONL 文件。"""
    if not CLAUDE_PROJECTS_DIR.exists():
        return None

    for project_dir in CLAUDE_PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        jsonl_file = project_dir / f"{session_id}.jsonl"
        if jsonl_file.exists():
            return jsonl_file
    return None


def _detect_claude_waiting_approval() -> bool:
    """检测 Claude 是否处于等待授权状态。

    逻辑：
    1. 读取活跃会话注册表获取 sessionId
    2. 读取对应 JSONL 文件尾部
    3. 检查最后的 assistant 消息：
       - stop_reason == "tool_use" 且后续无 tool_result → WAITING_APPROVAL
       - stop_reason == "end_turn" → IDLE
    """
    session = _get_active_claude_session()
    if not session:
        return False

    session_id = session.get("sessionId")
    if not session_id:
        return False

    jsonl_path = _find_claude_session_jsonl(session_id)
    if not jsonl_path:
        return False

    events = _read_jsonl_tail(jsonl_path)
    if not events:
        return False

    # 从后往前查找最后的 assistant 消息
    last_assistant = None
    last_assistant_idx = -1

    for i in range(len(events) - 1, -1, -1):
        evt = events[i]
        if evt.get("type") == "assistant":
            last_assistant = evt
            last_assistant_idx = i
            break

    if not last_assistant:
        return False

    # 检查 stop_reason
    message = last_assistant.get("message", {})
    stop_reason = message.get("stop_reason")

    if stop_reason != "tool_use":
        # stop_reason 是 end_turn 或其他 → 不在等待授权
        return False

    # stop_reason 是 tool_use，检查后续是否有 tool_result
    # tool_result 会在 assistant 消息之后作为 user 消息出现
    has_tool_result = False
    for i in range(last_assistant_idx + 1, len(events)):
        evt = events[i]
        if evt.get("type") == "user":
            msg = evt.get("message", {})
            content = msg.get("content", "")
            # tool_result 是 content 为 list 且包含 type: tool_result 的情况
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        has_tool_result = True
                        break
            if has_tool_result:
                break
        # 如果遇到下一个 assistant 消息，说明 tool_result 已处理
        if evt.get("type") == "assistant":
            break

    # tool_use 但无 tool_result → 等待授权
    return not has_tool_result


def check_claude() -> dict[str, Any]:
    """检测 Claude Code 状态（v1.5.0: 修正状态优先级）。

    优先级：
    1. STOPPED — 进程不存在
    2. WAITING_APPROVAL — 等待工具授权
    3. RUNNING — 有近期任务活动
    4. IDLE — 进程存在但无活动

    Returns:
        dict: {status, message, source, last_event, last_activity}
    """
    process_list = _tasklist()
    process_running = _process_exists(process_list, PROCESS_CLAUDE)

    # STOPPED: 进程不存在
    if not process_running:
        return {
            "status": AgentStatus.STOPPED,
            "message": "Claude Code 未运行",
            "source": "process_check",
            "last_event": None,
            "last_activity": "",
        }

    # WAITING_APPROVAL: 等待工具授权
    if _detect_claude_waiting_approval():
        return {
            "status": AgentStatus.WAITING_APPROVAL,
            "message": "Claude Code 等待授权",
            "source": "session_jsonl",
            "last_event": None,
            "last_activity": "waiting for approval",
        }

    # 检查活跃事件
    last_event_time = _get_last_claude_event_time()
    recently_active = _is_recently_active()
    last_activity = _format_last_activity(last_event_time)

    if recently_active:
        # RUNNING: 有近期活动
        elapsed = (datetime.now() - last_event_time).total_seconds() if last_event_time else 0
        return {
            "status": AgentStatus.RUNNING,
            "message": f"Claude Code 运行中 (活跃 {int(elapsed)}秒前)",
            "source": "session_jsonl",
            "last_event": last_event_time.isoformat() if last_event_time else None,
            "last_activity": last_activity,
        }

    # IDLE: 进程存在但无近期活动
    if last_event_time:
        elapsed = (datetime.now() - last_event_time).total_seconds()
        minutes_ago = int(elapsed // 60)
        return {
            "status": AgentStatus.IDLE,
            "message": f"Claude Code 空闲 (最后活跃 {minutes_ago}分钟前)",
            "source": "session_jsonl",
            "last_event": last_event_time.isoformat(),
            "last_activity": last_activity,
        }

    return {
        "status": AgentStatus.IDLE,
        "message": "Claude Code 空闲",
        "source": "session_jsonl",
        "last_event": None,
        "last_activity": "",
    }


def _get_latest_codex_session() -> Path | None:
    """获取最新的 Codex session rollout 文件。"""
    if not CODEX_SESSIONS_DIR.exists():
        return None

    latest_file = None
    latest_mtime = 0

    for year_dir in CODEX_SESSIONS_DIR.iterdir():
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
            for day_dir in month_dir.iterdir():
                if not day_dir.is_dir():
                    continue
                for f in day_dir.glob("rollout-*.jsonl"):
                    try:
                        mtime = f.stat().st_mtime
                        if mtime > latest_mtime:
                            latest_mtime = mtime
                            latest_file = f
                    except OSError:
                        continue

    return latest_file


def _codex_has_active_process() -> bool:
    """Return whether chat_processes.json contains a live osPid."""
    if not CODEX_CHAT_PROCESSES.exists():
        return False

    try:
        with open(CODEX_CHAT_PROCESSES, "r", encoding="utf-8") as f:
            processes = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    for proc in processes:
        try:
            pid = int(proc.get("osPid"))
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue

        try:
            os.kill(pid, 0)
        except PermissionError:
            # Permission denied still means that the process exists.
            return True
        except (OSError, ProcessLookupError):
            continue
        else:
            return True

    return False


def _codex_event_payload(event: dict[str, Any]) -> dict[str, Any]:
    """Return the payload for current and exported rollout event shapes."""
    payload = event.get("payload")
    if isinstance(payload, dict):
        return payload
    item = event.get("item")
    if isinstance(item, dict):
        return item
    return {}


def _codex_event_type(event: dict[str, Any]) -> str | None:
    payload = _codex_event_payload(event)
    return payload.get("type") or event.get("event_type")


def _codex_event_time(event: dict[str, Any]) -> datetime | None:
    """Parse a rollout event timestamp into local naive datetime."""
    payload = _codex_event_payload(event)
    value = event.get("timestamp") or event.get("ts") or payload.get("timestamp")
    if value is None:
        return None

    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000
        try:
            return datetime.fromtimestamp(seconds)
        except (OverflowError, OSError, ValueError):
            return None

    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _codex_rollout_events() -> tuple[Path | None, list[dict[str, Any]]]:
    """Load the latest rollout and enough history for an open task."""
    session_file = _get_latest_codex_session()
    if not session_file:
        return None, []
    try:
        # A long task can have task_started well before its latest tool call.
        events = _read_jsonl_tail(session_file, tail_bytes=2 * 1024 * 1024)
    except Exception:
        return session_file, []
    return session_file, events


def _codex_has_unfinished_task(events: list[dict[str, Any]]) -> bool:
    """Return true when the latest task_started has no later task_complete."""
    last_started = -1
    last_completed = -1
    for index, event in enumerate(events):
        event_type = _codex_event_type(event)
        if event_type == "task_started":
            last_started = index
        elif event_type == "task_complete":
            last_completed = index
    return last_started > last_completed


def _codex_rollout_recently_active() -> bool:
    """Return true when the latest rollout has an event within five minutes."""
    session_file, events = _codex_rollout_events()
    if not session_file:
        return False

    latest_event_time = None
    for event in events:
        event_time = _codex_event_time(event)
        if event_time and (latest_event_time is None or event_time > latest_event_time):
            latest_event_time = event_time

    if latest_event_time is None:
        try:
            latest_event_time = datetime.fromtimestamp(session_file.stat().st_mtime)
        except OSError:
            return False

    return (datetime.now() - latest_event_time).total_seconds() <= ACTIVE_TIMEOUT_SECONDS


def _detect_codex_waiting_approval() -> bool:
    """Return true when the latest custom_tool_call has no output yet."""
    _, events = _codex_rollout_events()
    if not events:
        return False

    tool_call_ids = set()
    tool_output_call_ids = set()
    latest_task_complete = -1
    latest_pending_call_index = -1
    latest_approval_call_index = -1

    for index, event in enumerate(events):
        event_type = _codex_event_type(event)
        payload = _codex_event_payload(event)
        if event_type == "task_complete":
            latest_task_complete = index
        elif event_type == "custom_tool_call":
            call_id = payload.get("call_id")
            if call_id:
                tool_call_ids.add(call_id)
        elif event_type == "custom_tool_call_output":
            call_id = payload.get("call_id")
            if call_id:
                tool_output_call_ids.add(call_id)

    pending_call_ids = tool_call_ids - tool_output_call_ids
    if not pending_call_ids:
        return False

    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        if _codex_event_type(event) != "custom_tool_call":
            continue
        call_id = _codex_event_payload(event).get("call_id")
        if call_id in pending_call_ids:
            latest_pending_call_index = index
            status = payload.get("status")
            approval_state = payload.get("approval") or payload.get("permission")
            # A completed custom_tool_call without output is an in-flight
            # execution.  Approval waits expose a non-completed status or an
            # explicit approval/permission state.
            if status not in ("completed", "failed", "cancelled") or approval_state:
                latest_approval_call_index = index
            break

    # An old call that is followed by a completed task is not an approval wait.
    return latest_approval_call_index > latest_task_complete


def check_codex() -> dict[str, Any]:
    """Detect Codex Desktop status without changing Claude/MiMo monitors."""
    process_list = _tasklist()
    process_running = _process_exists(process_list, PROCESS_CODEX)
    managed_process_running = _codex_has_active_process()
    _, events = _codex_rollout_events()
    unfinished_task = _codex_has_unfinished_task(events)
    rollout_active = _codex_rollout_recently_active()

    if _detect_codex_waiting_approval():
        return {
            "status": AgentStatus.WAITING_APPROVAL,
            "message": "Codex Desktop waiting for approval",
            "source": "session_jsonl",
            "last_activity": "waiting for approval",
        }

    if managed_process_running or rollout_active or unfinished_task:
        source = "process_manager" if managed_process_running else "session_jsonl"
        return {
            "status": AgentStatus.RUNNING,
            "message": "Codex Desktop running",
            "source": source,
            "last_activity": "",
        }

    if process_running:
        return {
            "status": AgentStatus.IDLE,
            "message": "Codex Desktop idle",
            "source": "process_check",
            "last_activity": "",
        }

    return {
        "status": AgentStatus.STOPPED,
        "message": "Codex Desktop stopped",
        "source": "process_check",
        "last_activity": "",
    }

def _mimo_db_state() -> tuple[bool, bool, bool]:
    """Return (has_recent_session, has_active_tool, all_tools_terminal)."""
    if not MIMO_DB_FILE.exists():
        return False, False, False

    connection = None
    try:
        db_uri = MIMO_DB_FILE.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(db_uri, uri=True, timeout=1)
        session_row = connection.execute(
            """
            SELECT id
            FROM session
            WHERE parent_id IS NULL
            ORDER BY time_updated DESC
            LIMIT 1
            """
        ).fetchone()
        if not session_row:
            return False, False, False

        session_id = session_row[0]
        has_active_tool = False
        all_tools_terminal = True

        rows = connection.execute(
            """
            SELECT data
            FROM part
            WHERE session_id = ?
            ORDER BY time_updated DESC
            """,
            (session_id,),
        )
        for (raw_data,) in rows:
            try:
                data = json.loads(raw_data)
            except (TypeError, json.JSONDecodeError):
                continue

            if data.get("type") != "tool":
                continue

            state = data.get("state") or {}
            status = state.get("status")
            if status in ("running", "pending"):
                has_active_tool = True
                all_tools_terminal = False
            elif status not in ("completed", "error"):
                all_tools_terminal = False

        return True, has_active_tool, all_tools_terminal
    except (OSError, sqlite3.Error):
        return False, False, False
    finally:
        if connection is not None:
            connection.close()

def _scan_mimo_permission_log(log_path: Path) -> tuple[set[str], set[str]]:
    """Read one MiMo log incrementally and return asking/replied permission IDs."""
    try:
        stat = log_path.stat()
    except OSError:
        return set(), set()

    cache_key = str(log_path)
    cached = _MIMO_PERMISSION_LOG_CACHE.get(cache_key)
    incremental = (
        cached is not None
        and stat.st_size >= cached["offset"]
        and stat.st_mtime_ns >= cached["mtime_ns"]
    )

    asking: set[str]
    replied: set[str]
    if incremental:
        asking = set(cached["asking"])
        replied = set(cached["replied"])
        try:
            with log_path.open("rb") as handle:
                handle.seek(cached["offset"])
                raw = cached["partial"].encode("utf-8") + handle.read()
            text = raw.decode("utf-8", errors="replace")
        except OSError:
            return asking, replied
    else:
        asking = set()
        replied = set()
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return asking, replied

    lines = text.splitlines(keepends=True)
    partial = ""
    if lines and not lines[-1].endswith(("\n", "\r")):
        partial = lines.pop()

    for line in lines:
        ask_match = _MIMO_PERMISSION_ASK_RE.search(line)
        if ask_match:
            asking.add(ask_match.group(1))
        reply_match = _MIMO_PERMISSION_REPLY_RE.search(line)
        if reply_match:
            replied.add(reply_match.group(1))

    _MIMO_PERMISSION_LOG_CACHE[cache_key] = {
        "offset": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "partial": partial,
        "asking": asking,
        "replied": replied,
    }
    return asking, replied


def _mimo_has_pending_permission() -> bool:
    """Return True for an asking permission that has no matching reply."""
    if not MIMO_LOG_DIR.exists():
        return False

    asking: set[str] = set()
    replied: set[str] = set()
    try:
        log_files = sorted(MIMO_LOG_DIR.glob("*.log"))
    except OSError:
        return False

    for log_path in log_files:
        file_asking, file_replied = _scan_mimo_permission_log(log_path)
        asking.update(file_asking)
        replied.update(file_replied)

    return bool(asking - replied)


def check_mimo() -> dict[str, Any]:
    """Check MiMo Code status using its latest main session.

    Priority:
        STOPPED > WAITING_APPROVAL > RUNNING > IDLE
    """
    process_list = _tasklist()
    running = _process_exists(process_list, PROCESS_MIMO)

    # STOPPED: the MiMo process is not present.
    if not running:
        return {
            "status": AgentStatus.STOPPED,
            "message": "MiMo Code not running",
            "source": "process_check",
            "last_activity": "",
        }

    # WAITING_APPROVAL: an asking permission has no matching reply.
    if _mimo_has_pending_permission():
        return {
            "status": AgentStatus.WAITING_APPROVAL,
            "message": "MiMo Code waiting for approval",
            "source": "mimocode_permission_log",
            "last_activity": "waiting for approval",
        }

    has_session, has_active_tool, all_tools_terminal = _mimo_db_state()

    # RUNNING: the latest main session has a running or pending tool part.
    if has_active_tool:
        return {
            "status": AgentStatus.RUNNING,
            "message": "MiMo Code running",
            "source": "mimocode_db_part",
            "last_activity": "tool running or pending",
        }

    # IDLE: the latest main session exists and every tool is terminal.
    if has_session and all_tools_terminal:
        return {
            "status": AgentStatus.IDLE,
            "message": "MiMo Code idle",
            "source": "mimocode_db",
            "last_activity": "",
        }

    return {
        "status": AgentStatus.IDLE,
        "message": "MiMo Code idle",
        "source": "mimocode_db_no_active_tool",
        "last_activity": "",
    }

def check_all() -> dict[str, dict[str, Any]]:
    """检测所有 Agent 状态。

    Returns:
        dict: {claude: {...}, codex: {...}, mimo: {...}}
    """
    return {
        "claude": check_claude(),
        "codex": check_codex(),
        "mimo": check_mimo(),
    }


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行测试"""
    print("=== Agent Health Checker (v1.5.0) ===")
    print()

    results = check_all()

    for agent_id, result in results.items():
        status = result["status"]
        message = result["message"]
        last_activity = result.get("last_activity", "")
        activity_str = f" [active: {last_activity}]" if last_activity else ""
        print(f"  {agent_id.upper()}: {status} — {message}{activity_str}")

    print()


if __name__ == "__main__":
    main()
