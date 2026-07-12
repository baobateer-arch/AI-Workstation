"""Kindle WiFi 图片服务器。"""

from __future__ import annotations

import socket
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 图片路径
IMAGE_PATH = PROJECT_ROOT / "output" / "dashboard_kindle.png"

# 默认端口
DEFAULT_PORT = 8765


def get_local_ip() -> str:
    """获取本机局域网 IP"""
    try:
        # 创建一个 UDP socket 连接到外部地址（不会真的发送数据）
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    def do_GET(self):
        """处理 GET 请求"""
        if self.path == "/dashboard.png":
            self._serve_image()
        else:
            self.send_error(404, "Not Found")

    def _serve_image(self):
        """返回图片"""
        if not IMAGE_PATH.exists():
            self.send_error(404, "Dashboard image not found")
            return

        try:
            image_data = IMAGE_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(image_data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(image_data)
        except Exception as e:
            self.send_error(500, f"Error serving image: {e}")

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"  [{self.log_date_time_string()}] {format % args}")


def run_server(port: int = DEFAULT_PORT):
    """
    启动图片服务器。

    Args:
        port: 监听端口
    """
    # 检查图片是否存在
    if not IMAGE_PATH.exists():
        print(f"[WARNING] Image not found: {IMAGE_PATH}")
        print("          Server will start but return 404 for /dashboard.png")
        print()

    # 获取本机 IP
    local_ip = get_local_ip()

    # 启动服务器
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)

    print("=== Kindle Server ===")
    print()
    print(f"Image: {IMAGE_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Server: RUNNING")
    print(f"URL: http://{local_ip}:{port}/dashboard.png")
    print()
    print("Press Ctrl+C to stop")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        print("=== Server Stopped ===")
        server.shutdown()


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    """命令行入口"""
    port = DEFAULT_PORT

    # 解析参数
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    run_server(port)


if __name__ == "__main__":
    main()
