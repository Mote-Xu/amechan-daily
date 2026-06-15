"""
HTTP 服务器 v4 — 完全无状态 + 多线程 + 频率限制
"""
import json
import random
import sys
import time
from collections import defaultdict
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import HOST, PORT, STATIC_DIR, DATA_DIR, ROOT_DIR
from generator import generate_timeline, generate_jine_chat, generate_jine_release_msgs


# ============================================================
# 频率限制（内存，重启清零）
# ============================================================
_ip_last_request: dict[str, float] = defaultdict(float)
_ip_daily_count: dict[str, int] = defaultdict(int)
RATE_INTERVAL = 5       # 同一 IP 两次请求最小间隔（秒）
RATE_DAILY_CAP = 100    # 同一 IP 每天最大 POST 次数


def check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    if now - _ip_last_request[client_ip] < RATE_INTERVAL:
        return False
    if _ip_daily_count[client_ip] >= RATE_DAILY_CAP:
        return False
    _ip_last_request[client_ip] = now
    _ip_daily_count[client_ip] += 1
    return True


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

    def _get_client_ip(self) -> str:
        # 优先取 X-Forwarded-For（Cloudflare 代理后会加）
        forwarded = self.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0]

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
            # v4: stateless — frontend manages timeline via localStorage
            self._send_json({"count": 0, "pool_remaining": 0, "timeline": []})
        elif path == "/api/feed":
            self._send_json({"count": 0, "pool": 0, "feed": []})
        elif path == "/api/jine/chat":
            # v4: frontend manages JINE via localStorage
            self._send_json({"chat": []})
        elif path == "/api/stats":
            self._send_json({"count": 0, "pool": 0, "status": "ok"})
        elif path == "/data/feed.json":
            # Static fallback
            self._send_json({"timeline": [], "hidden_pool": [], "jine_chat": []})
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Rate limit all POST endpoints (they call DeepSeek)
        client_ip = self._get_client_ip()
        if not check_rate_limit(client_ip):
            self._send_json({"ok": False, "error": "超天酱正在休息，请稍后再来～"}, status=429)
            return

        if path == "/api/generate":
            body_raw = self._read_body()
            body = self._parse_json(body_raw) if body_raw else {}

            topic = body.get("topic", None)
            print(f"\n[*] POST /api/generate (stateless) | topic: {topic or '随机'}")

            try:
                data = generate_timeline(topic)
                # v4: return JSON only, frontend saves to localStorage
                self._send_json({
                    "ok": True,
                    "event": data.get("event", topic),
                    "timeline": data.get("timeline", []),
                    "hidden_pool": data.get("hidden_pool", []),
                })
            except Exception as e:
                print(f"  [X] 生成失败: {e}")
                self._send_json({"ok": False, "error": "生成失败，请稍后重试"}, status=500)

        elif path == "/api/release":
            # v4 stateless: frontend sends poketter text, backend generates JINE release msgs
            body_raw = self._read_body()
            body = self._parse_json(body_raw) if body_raw else None
            if not body:
                self._send_json({"ok": False, "error": "invalid JSON body"}, status=400)
                return

            poke_text = body.get("poke_text", "")
            diary_text = body.get("diary_text", "")
            print(f"\n[*] POST /api/release (stateless) | poke: {poke_text[:30] if poke_text else '(empty)'}")

            if not poke_text:
                self._send_json({"ok": False, "error": "missing poke_text"}, status=400)
                return

            try:
                msg_count = random.randint(2, 5)
                msgs = generate_jine_release_msgs(poke_text, diary_text, count=msg_count)
                jine_msgs = []
                for m in msgs:
                    if m.get("reply"):
                        jine_msgs.append({
                            "reply": m["reply"],
                            "ame_sticker": m.get("ame_sticker"),
                            "time": time.strftime("%H:%M"),
                        })
                self._send_json({"ok": True, "jine_msgs": jine_msgs})
            except Exception as e:
                print(f"  [X] JINE 释放消息生成失败: {e}")
                self._send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/jine/chat":
            # v4: already stateless — no changes needed
            body_raw = self._read_body()
            body = self._parse_json(body_raw) if body_raw else {}

            text = body.get("text", "")
            sticker = body.get("sticker", "")
            history = body.get("history", [])

            if not text and not sticker:
                self._send_json({"ok": False, "error": "missing text or sticker"}, status=400)
                return

            is_pure_sticker = bool(sticker) and not text.replace("[...]", "").strip()
            tag = f"sticker:{sticker}" if is_pure_sticker else f"text:{text[:30]}"
            print(f"\n[*] POST /api/jine/chat | {tag} | history: {len(history)} msgs")

            try:
                result = generate_jine_chat(text=text, sticker=sticker, history=history)
                resp = {
                    "ok": True,
                    "reply": result.get("reply", ""),
                    "time": time.strftime("%H:%M"),
                }
                if result.get("ame_sticker"):
                    resp["ame_sticker"] = result["ame_sticker"]
                self._send_json(resp)
            except Exception as e:
                print(f"  [X] JINE 回复失败: {e}")
                self._send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/clear":
            # v4 stateless: no-op
            print("\n[*] /api/clear — no-op (stateless)")
            self._send_json({"ok": True})

        else:
            self.send_error(404, "Not Found")

    def _read_body(self) -> bytes | None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length:
                return self.rfile.read(content_length)
        except Exception:
            pass
        return None

    def _parse_json(self, raw: bytes) -> dict | None:
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("  + Poketter v4.0 — Stateless + Threading + Rate Limiter +")
    print("=" * 50)
    print(f"  地址: http://{HOST}:{PORT}")
    print(f"  API:  GET  /api/timeline   -> 空（前端 localStorage）")
    print(f"       POST /api/generate    -> 生成 + 返回 JSON（不写盘）")
    print(f"       POST /api/release     -> F7 JINE 消息（无状态）")
    print(f"       POST /api/jine/chat   -> F8 聊天回复（无状态）")
    print(f"  安全: IP 限频 {RATE_INTERVAL}s/{RATE_DAILY_CAP}次每天")
    print("=" * 50)

    server = ThreadingHTTPServer((HOST, PORT), AmechanHandler)
    server.allow_reuse_address = True

    print(f"\n[*] 服务器启动中...\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[~] 超天酱下线~ 明天见!")
        server.shutdown()


if __name__ == "__main__":
    main()
