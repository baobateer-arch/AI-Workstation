"""AI Workstation 自动刷新调度器。"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 状态文件路径
DATA_DIR = PROJECT_ROOT / "data"
STATE_FILE = DATA_DIR / "scheduler_state.json"

# 默认刷新间隔（秒）
DEFAULT_INTERVAL = 60


def _format_time(dt: datetime) -> str:
    """格式化时间"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _save_state(state: dict) -> None:
    """保存调度器状态"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_state() -> dict:
    """加载调度器状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _run_workstation() -> bool:
    """运行一次 workstation"""
    try:
        from app.workstation import main
        return main() == 0
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def _seconds_until_next_minute() -> float:
    """计算距离下一分钟00秒的等待时间"""
    now = datetime.now()
    seconds = 60 - now.second - now.microsecond / 1_000_000
    return seconds


def run_scheduler(interval: int = DEFAULT_INTERVAL):
    """
    运行调度器。

    Args:
        interval: 刷新间隔（秒）
    """
    start_time = datetime.now()
    run_count = 0
    last_update = None

    print("=== AI Workstation Scheduler ===")
    print(f"Start: {_format_time(start_time)}")
    print(f"Interval: {interval}s (aligned to minute)")
    print("Press Ctrl+C to stop")
    print()

    # 保存启动状态
    _save_state({
        "started_at": _format_time(start_time),
        "runs": 0,
        "last_run": None,
        "next_run": None,
        "status": "running",
        "interval": interval,
    })

    try:
        # 启动后立即执行一次刷新
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Running...")
        success = _run_workstation()

        run_count = 1
        last_update = datetime.now()

        # 计算下一次更新（下一分钟00秒）
        next_ts = last_update.timestamp() + _seconds_until_next_minute()
        next_update = datetime.fromtimestamp(next_ts)

        # 显示状态
        print()
        print(f"  Runs: {run_count}")
        print(f"  Last: {_format_time(last_update)}")
        print(f"  Next: {_format_time(next_update)}")
        print()

        # 保存状态
        _save_state({
            "started_at": _format_time(start_time),
            "runs": run_count,
            "last_run": _format_time(last_update),
            "next_run": _format_time(next_update),
            "status": "running",
            "interval": interval,
        })

        # 等待到下一分钟00秒
        wait = _seconds_until_next_minute()
        if wait > 0.5:
            print(f"  Waiting {wait:.1f}s to align to next minute...")
            time.sleep(wait)

        # 主循环：每分钟00秒刷新
        while True:
            # 执行 workstation
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Running...")
            success = _run_workstation()

            run_count += 1
            last_update = datetime.now()

            # 计算下一次更新（下一分钟00秒）
            next_ts = last_update.timestamp() + _seconds_until_next_minute()
            next_update = datetime.fromtimestamp(next_ts)

            # 显示状态
            print()
            print(f"  Runs: {run_count}")
            print(f"  Last: {_format_time(last_update)}")
            print(f"  Next: {_format_time(next_update)}")
            print()

            # 保存状态
            _save_state({
                "started_at": _format_time(start_time),
                "runs": run_count,
                "last_run": _format_time(last_update),
                "next_run": _format_time(next_update),
                "status": "running",
                "interval": interval,
            })

            # 等待到下一分钟00秒
            wait = _seconds_until_next_minute()
            if wait > 0.5:
                print(f"  Waiting {wait:.1f}s to align to next minute...")
                time.sleep(wait)

    except KeyboardInterrupt:
        print()
        print("=== Scheduler Stopped ===")
        print(f"Total runs: {run_count}")
        if last_update:
            print(f"Last update: {_format_time(last_update)}")

        # 保存停止状态
        _save_state({
            "started_at": _format_time(start_time),
            "runs": run_count,
            "last_run": _format_time(last_update) if last_update else None,
            "next_run": None,
            "status": "stopped",
            "interval": interval,
        })


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行入口"""
    interval = DEFAULT_INTERVAL

    # 解析参数
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
            if interval < 60:
                interval = 60
        except ValueError:
            pass

    run_scheduler(interval)


if __name__ == "__main__":
    main()
