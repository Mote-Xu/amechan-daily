"""
HTTP 服务器 — API + 静态文件服务
使用 Python 内置 http.server，零新依赖。
启动后访问 http://127.0.0.1:7860
"""
import json
import sys
import time

# 修复 Windows 控制台 UTF-8 编码
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from config import HOST, PORT, STATIC_DIR
from feed import get_feed, feed_count
from generator import generate_and_save


class AmechanHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器：路由 API + 静态文件。"""

    def __init__(self, *args, **kwargs):
        # 静态文件根目录设为 static/
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    # ---- CORS & 通用头部 ----
    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, path: str):
        """发送 HTML 文件。"""
        full_path = STATIC_DIR / path
        if not full_path.exists():
            self.send_error(404, "Not Found")
            return
        body = full_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors()
        self.end_headers()
        self.wfile.write(body)

    # ---- 日志 ----
    def log_message(self, format, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] {args[0]}")

    # ---- 路由 ----
    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._send_html("index.html")
        elif path == "/api/feed":
            feed = get_feed()
            self._send_json({"count": len(feed), "feed": feed})
        elif path == "/api/stats":
            self._send_json({"count": feed_count(), "status": "ok"})
        else:
            # 尝试作为静态文件处理
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/generate":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body_raw = self.rfile.read(content_length) if content_length else b"{}"
                body = json.loads(body_raw.decode("utf-8")) if body_raw else {}
            except json.JSONDecodeError:
                body = {}

            topic = body.get("topic", None)
            print(f"\n[*] POST /api/generate 触发 | topic: {topic or '随机'}")

            try:
                entry = generate_and_save(topic)
                self._send_json({"ok": True, "entry": entry})
            except Exception as e:
                print(f"  [X] 生成失败: {e}")
                self._send_json({"ok": False, "error": str(e)}, status=500)
        else:
            self.send_error(404, "Not Found")


def main():
    """启动 HTTP 服务器。"""
    # 确保数据目录存在
    from config import DATA_DIR
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("  + 超天酱日常推文小站 -- Amechan Daily +")
    print("=" * 50)
    print(f"  地址: http://{HOST}:{PORT}")
    print(f"  API:  GET  /api/feed     -> 获取推文列表")
    print(f"       POST /api/generate  -> 生成新推文对")
    print("=" * 50)

    # 首次启动时如果 feed 为空，自动生成一条
    if feed_count() == 0:
        print("\n[!] Feed 为空，自动生成首条推文...")
        try:
            generate_and_save()
        except Exception as e:
            print(f"  [!] 首条生成失败（可能是 API Key 未配置）: {e}")
            print("  服务器仍会启动，但需要先配置 .env 中的 API Key")

    print(f"\n[*] 服务器启动中...\n")

    server = HTTPServer((HOST, PORT), AmechanHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[~] 超天酱下线啦~ 明天见!")
        server.shutdown()


if __name__ == "__main__":
    main()
