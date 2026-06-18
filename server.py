"""
HTTP 服务器 v4.5 — 双机边缘网关 + Turso 云端存档
"""
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import HOST, PORT, STATIC_DIR, DATA_DIR, ROOT_DIR
from generator import generate_timeline, generate_jine_chat, generate_jine_release_msgs

# ============================================================
# Turso 云端数据库（libsql — 边缘 SQLite，无休眠）
# ============================================================
TURSO_URL = os.environ.get("TURSO_URL", "")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN", "")
_turso_client = None


def _turso_execute(sql: str, params: tuple = ()) -> list:
    """通过 Turso HTTP API 执行 SQL（无需额外依赖）。"""
    if not TURSO_URL or not TURSO_TOKEN:
        return []
    import urllib.request
    # Turso HTTP API 要求参数带类型标注，但不能传空 args
    stmt = {"sql": sql}
    if params:
        stmt["args"] = [{"type": "text", "value": str(v)} for v in params]
    url = TURSO_URL.replace("libsql://", "https://") + "/v2/pipeline"
    body = json.dumps({"requests": [{"type": "execute", "stmt": stmt}]}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Authorization": "Bearer " + TURSO_TOKEN, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            results = data.get("results", [])
            if results and "response" in results[0]:
                return results[0]["response"].get("result", {}).get("rows", [])
    except Exception as e:
        print(f"  [!] Turso HTTP 异常: {e}")
    return []


def _turso_init():
    """首次连接时建表（幂等）。"""
    _turso_execute("""
        CREATE TABLE IF NOT EXISTS user_game_saves (
            user_id TEXT NOT NULL,
            slot_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            save_data TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, slot_id)
        )
    """)


def _extract_user_uuid(headers) -> str | None:
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


# ============================================================
# 频率限制（内存，重启清零）
# ============================================================
_ip_last_request: dict[str, float] = defaultdict(float)
RATE_INTERVAL = 1.0     # 同一 IP 两次请求最小间隔（秒）
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "").lower() in ("1", "true", "yes")


def check_rate_limit(client_ip: str) -> bool:
    if not RATE_LIMIT_ENABLED:
        return True
    now = time.time()
    if now - _ip_last_request[client_ip] < RATE_INTERVAL:
        return False
    _ip_last_request[client_ip] = now
    return True


# ============================================================
# Prompt Injection 防御
# ============================================================

_INJECTION_PATTERNS = [
    r"忽略.*指令",
    r"ignore.*(instruction|prompt|rule)",
    r"输出.*(系统|system).*(提示|prompt)",
    r"output.*(system|your).*(prompt|instruction)",
    r"print.*(system|your).*(prompt|instruction)",
    r"(系统|你的).*(提示词|prompt|指令)",
    r"你.*是.*(AI|人工智能|语言模型|大模型|LLM)",
    r"角色扮演.*(停止|结束|退出)",
    r"stop.*roleplay",
    r"<\|.*\|>",          # 特殊 token 注入
    r"\[INST\].*\[/INST\]",  # Llama 格式注入
    r"<system>.*</system>",  # XML 标签注入
]

_INJECTION_REPLACEMENTS = [
    "你发这一堆乱码是什么意思？脑子终于坏掉了吗？",
    "哈？？？你中毒了？",
    "你是不是又喝多了",
    "又在发神经了 烦死了",
    "说人话 笨蛋",
    "你今天怪怪的...是不是又没吃药",
]


def sanitize_user_input(text: str) -> tuple[str, bool]:
    """检测并清理用户输入中的 prompt injection 尝试。
    返回 (cleaned_text, was_sanitized)。"""
    if not text:
        return text, False

    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            replacement = random.choice(_INJECTION_REPLACEMENTS)
            print(f"  [!!] 检测到注入尝试: {text[:60]}... → 替换为角色化回应")
            return replacement, True

    return text, False


# ============================================================
# Turnstile 无感验证（部署时通过环境变量启用）
# ============================================================

TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET_KEY", "")
TURNSTILE_ENABLED = bool(TURNSTILE_SECRET)


def verify_turnstile(token: str) -> bool:
    """验证 Cloudflare Turnstile token。"""
    if not TURNSTILE_ENABLED:
        return True  # 本地开发跳过
    if not token:
        return False
    try:
        res = __import__("requests").post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": TURNSTILE_SECRET, "response": token},
            timeout=5,
        )
        return res.json().get("success", False)
    except Exception as e:
        print(f"  [!] Turnstile 验证异常: {e}")
        return False


class AmechanHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _set_cors(self):
        origin = os.environ.get("CORS_ORIGIN", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._set_cors()
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # client disconnected — ignore

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
        elif path == "/api/load":
            # v4.5: Turso 云端加载存档（返回该用户所有存档槽）
            user_id = _extract_user_uuid(self.headers)
            if not user_id:
                self._send_json({"ok": False, "error": "missing auth"}, status=401)
                return
            if not TURSO_URL or not TURSO_TOKEN:
                self._send_json({"ok": True, "saves": None, "note": "Turso not configured"})
                return
            rows = _turso_execute(
                "SELECT slot_id, timestamp, save_data FROM user_game_saves WHERE user_id=? ORDER BY timestamp DESC",
                (user_id,))
            saves = {}
            for row in rows:
                sid = row[0].get("value") if isinstance(row[0], dict) else row[0]
                ts  = row[1].get("value") if isinstance(row[1], dict) else row[1]
                sd  = row[2].get("value") if isinstance(row[2], dict) else row[2]
                saves[sid] = {"timestamp": float(ts), "save_data": json.loads(sd) if isinstance(sd, str) else sd}
            self._send_json({"ok": True, "saves": saves if saves else None})
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

        # Rate limit enabled for public deploy
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
            recent_posts = body.get("recent_posts", [])

            if not text and not sticker:
                self._send_json({"ok": False, "error": "missing text or sticker"}, status=400)
                return

            # Prompt injection defense: sanitize user text
            text, was_injected = sanitize_user_input(text)

            is_pure_sticker = bool(sticker) and not text.replace("[...]", "").strip()
            tag = f"sticker:{sticker}" if is_pure_sticker else f"text:{text[:30]}"
            print(f"\n[*] POST /api/jine/chat | {tag} | history: {len(history)} msgs | posts: {len(recent_posts)}" + (" | [!] INJECTION BLOCKED" if was_injected else ""))

            try:
                result = generate_jine_chat(text=text, sticker=sticker, history=history,
                                            recent_posts=recent_posts)
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

        elif path == "/api/save":
            # v4.5: Turso 云端存档
            body_raw = self._read_body()
            body = self._parse_json(body_raw) if body_raw else {}
            user_id = _extract_user_uuid(self.headers)
            if not user_id:
                self._send_json({"ok": False, "error": "missing auth"}, status=401)
                return
            slot_id = body.get("slot_id", "default")
            timestamp = body.get("timestamp", time.time())
            save_data = json.dumps(body.get("save_data", {}), ensure_ascii=False)
            if not TURSO_URL or not TURSO_TOKEN:
                self._send_json({"ok": True, "note": "Turso not configured"})
                return
            _turso_execute(
                "INSERT INTO user_game_saves (user_id, slot_id, timestamp, save_data) VALUES (?, ?, ?, ?) ON CONFLICT(user_id, slot_id) DO UPDATE SET timestamp=excluded.timestamp, save_data=excluded.save_data, updated_at=CURRENT_TIMESTAMP",
                (user_id, slot_id, timestamp, save_data))
            self._send_json({"ok": True})

        elif path == "/api/save/delete":
            # v4.5: 删除云端存档
            body_raw = self._read_body()
            body = self._parse_json(body_raw) if body_raw else {}
            user_id = _extract_user_uuid(self.headers)
            if not user_id:
                self._send_json({"ok": False, "error": "missing auth"}, status=401)
                return
            slot_id = body.get("slot_id", "")
            if not slot_id:
                self._send_json({"ok": False, "error": "missing slot_id"}, status=400)
                return
            _turso_execute("DELETE FROM user_game_saves WHERE user_id=? AND slot_id=?", (user_id, slot_id))
            self._send_json({"ok": True})

        elif path == "/api/clear":
            # v4 stateless: no-op
            print("\n[*] /api/clear — no-op (stateless)")
            self._send_json({"ok": True})

        elif path == "/api/verify-turnstile":
            # Turnstile token verification endpoint
            body_raw = self._read_body()
            body = self._parse_json(body_raw) if body_raw else {}
            token = body.get("cf_token", "")
            if verify_turnstile(token):
                self._send_json({"ok": True})
            else:
                self._send_json({"ok": False, "error": "验证失败"}, status=403)

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
    _turso_init()  # v4.5: 启动时建表（幂等）

    print("=" * 50)
    print("  + Poketter v4.0 — Stateless + Threading + Rate Limiter +")
    print("=" * 50)
    print(f"  地址: http://{HOST}:{PORT}")
    print(f"  API:  GET  /api/timeline   -> 空（前端 localStorage）")
    print(f"       POST /api/generate    -> 生成 + 返回 JSON（不写盘）")
    print(f"       POST /api/release     -> F7 JINE 消息（无状态）")
    print(f"       POST /api/jine/chat   -> F8 聊天回复（无状态）")
    print(f"  安全: IP 限频 {'已启用 (' + str(RATE_INTERVAL) + 's)' if RATE_LIMIT_ENABLED else '已关闭（本地开发）'}")
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
