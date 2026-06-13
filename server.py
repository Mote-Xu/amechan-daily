"""
HTTP 服务器 v2 — Poketter 三层时间线 API
"""
import json
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from config import HOST, PORT, STATIC_DIR
from feed import get_timeline, pool_count, pop_from_pool, feed_count, clear_feed
from generator import generate_and_save, generate_single


class AmechanHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

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

    def log_message(self, format, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"[{ts}] {args[0]}")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._send_html("index.html")
        elif path == "/api/timeline":
            timeline = get_timeline()
            self._send_json({"count": len(timeline), "pool_remaining": pool_count(), "timeline": timeline})
        elif path == "/api/feed":
            # 旧版兼容
            timeline = get_timeline()
            pool = pool_count()
            self._send_json({"count": len(timeline), "pool": pool, "feed": timeline})
        elif path == "/api/stats":
            self._send_json({"count": feed_count(), "pool": pool_count(), "status": "ok"})
        else:
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
            print(f"\n[*] POST /api/generate | topic: {topic or '随机'}")

            try:
                data = generate_and_save(topic)
                self._send_json({"ok": True, "event": data.get("event"), "timeline_count": len(data.get("timeline", [])), "pool_count": len(data.get("hidden_pool", []))})
            except Exception as e:
                print(f"  [X] 生成失败: {e}")
                # 降级到旧版生成
                try:
                    print("  -> 降级到旧版生成...")
                    kangel, ame, topic = generate_single(topic)
                    from feed import save_tweet_pair
                    entry = save_tweet_pair(kangel, ame, topic)
                    self._send_json({"ok": True, "fallback": True, "entry": entry})
                except Exception as e2:
                    self._send_json({"ok": False, "error": str(e2)}, status=500)

        elif path == "/api/release":
            print("\n[*] POST /api/release — F7 伪生成")
            entry = pop_from_pool()
            if entry:
                print(f"  [OK] 释放: [{entry['layer']}] {entry['text'][:40]}... (剩余 {pool_count()})")
                self._send_json({"ok": True, "entry": entry, "pool_remaining": pool_count()})
            else:
                print("  [!] hidden_pool 已空，尝试生成...")
                try:
                    data = generate_and_save()
                    # 从新的 hidden_pool 再试一次
                    entry2 = pop_from_pool()
                    if entry2:
                        self._send_json({"ok": True, "entry": entry2, "pool_remaining": pool_count(), "regenerated": True})
                    else:
                        self._send_json({"ok": False, "error": "pool exhausted after regenerate"}, status=500)
                except Exception as e:
                    self._send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/clear":
            clear_feed()
            print("\n[*] 数据已清空")
            self._send_json({"ok": True})

        else:
            self.send_error(404, "Not Found")


def main():
    from config import DATA_DIR
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("  + Poketter v2.0 -- 三层时间线 +")
    print("=" * 50)
    print(f"  地址: http://{HOST}:{PORT}")
    print(f"  API:  GET  /api/timeline  -> 获取时间线")
    print(f"       POST /api/generate   -> 生成新批次")
    print(f"       POST /api/release    -> F7 释放 hidden_pool")
    print("=" * 50)

    if feed_count() == 0:
        print("\n[!] Feed 为空，自动生成首条...")
        try:
            generate_and_save()
        except Exception as e:
            print(f"  [!] 生成失败: {e}")

    print(f"\n[*] 服务器启动中...\n")
    server = HTTPServer((HOST, PORT), AmechanHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[~] 超天酱下线~ 明天见!")
        server.shutdown()


if __name__ == "__main__":
    main()
