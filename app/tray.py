"""AI Workstation Windows 托盘程序。"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pystray
from PIL import Image, ImageDraw


# 全局状态
_scheduler_thread: threading.Thread | None = None
_kindle_thread: threading.Thread | None = None
_kindle_server = None
_running = False


def _create_icon() -> Image.Image:
    """创建托盘图标"""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制一个简单的 "AI" 图标
    draw.rectangle((8, 8, 56, 56), fill=(50, 50, 50), outline=(200, 200, 200), width=2)
    draw.text((16, 18), "AI", fill=(255, 255, 255))
    return img


def _run_scheduler():
    """运行调度器"""
    try:
        from app.scheduler import run_scheduler
        run_scheduler()
    except Exception as e:
        print(f"[Scheduler Error] {e}")


def _run_kindle_server():
    """运行 Kindle 服务器"""
    try:
        from app.kindle_server import run_server
        run_server()
    except Exception as e:
        print(f"[Kindle Server Error] {e}")


def start_services():
    """启动所有服务"""
    global _scheduler_thread, _kindle_thread, _running

    if _running:
        return

    _running = True

    # 启动调度器
    _scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    _scheduler_thread.start()

    # 启动 Kindle 服务器
    _kindle_thread = threading.Thread(target=_run_kindle_server, daemon=True)
    _kindle_thread.start()

    print("[Tray] Services started")


def stop_services():
    """停止所有服务"""
    global _running
    _running = False
    print("[Tray] Services stopping...")


def restart_services():
    """重启所有服务"""
    stop_services()
    import time
    time.sleep(1)
    start_services()


def on_open_status(icon, item):
    """打开状态文件"""
    import subprocess
    state_file = PROJECT_ROOT / "data" / "scheduler_state.json"
    if state_file.exists():
        subprocess.Popen(["notepad", str(state_file)])
    else:
        print("[Tray] No state file found")


def on_restart(icon, item):
    """重启服务"""
    restart_services()


def on_stop(icon, item):
    """停止服务"""
    stop_services()


def on_quit(icon, item):
    """退出程序"""
    stop_services()
    icon.stop()


def main():
    """托盘程序入口"""
    print("=== AI Workstation Tray ===")
    print("Starting services...")

    # 创建图标
    icon = pystray.Icon(
        "AI Workstation",
        _create_icon(),
        "AI Workstation",
        menu=pystray.Menu(
            pystray.MenuItem("打开状态", on_open_status),
            pystray.MenuItem("重启服务", on_restart),
            pystray.MenuItem("停止服务", on_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", on_quit),
        ),
    )

    # 启动服务
    start_services()

    # 运行托盘（阻塞）
    icon.run()


if __name__ == "__main__":
    main()
