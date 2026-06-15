"""
HTTP 服务器 v2 — Poketter 三层时间线 API
"""
import json
import random
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote

from config import HOST, PORT, STATIC_DIR, DATA_DIR, ROOT_DIR
from feed import get_timeline, pool_count, pop_from_pool, feed_count, clear_feed, save_jine_message, get_jine_chat
from generator import generate_and_save, generate_single, generate_jine_reply, generate_jine_text_reply, generate_jine_release_msgs


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
        elif path == "/api/jine/chat":
            chat = get_jine_chat()
            self._send_json({"chat": chat})
        elif path == "/api/stats":
            self._send_json({"count": feed_count(), "pool": pool_count(), "status": "ok"})
        elif path == "/data/feed.json":
            # Static mode fallback: serve feed.json directly
            feed_path = DATA_DIR / "feed.json"
            if feed_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(feed_path.read_bytes())
            else:
                self._send_json({"timeline": [], "hidden_pool": [], "jine_chat": []})
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
            print("\n[*] POST /api/release — F7 戳一戳")
            entries = pop_from_pool()
            if entries:
                layers = [e['layer'] for e in entries]
                print(f"  [OK] 释放 {len(entries)} 条: {layers} (剩余 {pool_count()})")
                # 糖糖刚用超天酱和糖糖两个身份都发了动态，主动来 JINE 找阿P（2-5条）
                # v2.7: 使用专用的 release prompt — 明确玩家处于沉默状态
                jine_msgs = []
                poke_text = next((e['text'][:40] for e in entries if e['layer'] == 'poketter'), '刚才的动态')
                diary_text = next((e['text'][:40] for e in entries if e['layer'] == 'diary'), '')
                msg_count = random.randint(2, 5)
                msgs = generate_jine_release_msgs(poke_text, diary_text, count=msg_count)
                for m in msgs:
                    if m.get("reply"):
                        msg = save_jine_message(reply=m["reply"], ame_sticker=m.get("ame_sticker"), player_text="")
                        jine_msgs.append({"reply": m["reply"], "ame_sticker": m.get("ame_sticker"), "time": msg.get("time", time.strftime("%H:%M"))})
                self._send_json({"ok": True, "entries": entries, "pool_remaining": pool_count(), "jine_msgs": jine_msgs})
            else:
                print("  [!] hidden_pool 已空，尝试生成...")
                try:
                    data = generate_and_save()
                    entries2 = pop_from_pool()
                    if entries2:
                        jine_msgs = []
                        poke_text = next((e['text'][:40] for e in entries2 if e['layer'] == 'poketter'), '刚才的动态')
                        diary_text = next((e['text'][:40] for e in entries2 if e['layer'] == 'diary'), '')
                        msg_count = random.randint(2, 5)
                        msgs = generate_jine_release_msgs(poke_text, diary_text, count=msg_count)
                        for m in msgs:
                            if m.get("reply"):
                                msg = save_jine_message(reply=m["reply"], ame_sticker=m.get("ame_sticker"), player_text="")
                                jine_msgs.append({"reply": m["reply"], "ame_sticker": m.get("ame_sticker"), "time": msg.get("time", time.strftime("%H:%M"))})
                        self._send_json({"ok": True, "entries": entries2, "pool_remaining": pool_count(), "regenerated": True, "jine_msgs": jine_msgs})
                    else:
                        self._send_json({"ok": False, "error": "pool exhausted after regenerate"}, status=500)
                except Exception as e:
                    self._send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/clear":
            clear_feed()
            print("\n[*] 数据已清空")
            self._send_json({"ok": True})

        elif path == "/api/jine/send":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body_raw = self.rfile.read(content_length) if content_length else b"{}"
                body = json.loads(body_raw.decode("utf-8")) if body_raw else {}
            except json.JSONDecodeError:
                body = {}

            sticker = body.get("sticker", "")
            if not sticker:
                self._send_json({"ok": False, "error": "missing sticker"}, status=400)
                return

            print(f"\n[*] POST /api/jine/send | sticker: {sticker}")

            try:
                reply, ame_sticker = generate_jine_reply(sticker)
                msg = save_jine_message(sticker, reply, ame_sticker)
                resp = {"ok": True, "sticker": sticker, "reply": reply, "time": msg.get("time"), "recall": msg.get("recall", False)}
                if ame_sticker:
                    resp["ame_sticker"] = ame_sticker
                self._send_json(resp)
            except Exception as e:
                print(f"  [X] JINE 回复失败: {e}")
                self._send_json({"ok": False, "error": str(e)}, status=500)

        elif path == "/api/jine/text":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body_raw = self.rfile.read(content_length) if content_length else b"{}"
                body = json.loads(body_raw.decode("utf-8")) if body_raw else {}
            except json.JSONDecodeError:
                body = {}

            player_text = body.get("text", "").strip()
            if not player_text:
                self._send_json({"ok": False, "error": "missing text"}, status=400)
                return

            print(f"\n[*] POST /api/jine/text | text: {player_text[:30]}...")

            try:
                reply, ame_sticker = generate_jine_text_reply(player_text)
                msg = save_jine_message(reply=reply, ame_sticker=ame_sticker, player_text=player_text)
                resp = {"ok": True, "player_text": player_text, "reply": reply, "time": msg.get("time"), "recall": msg.get("recall", False)}
                if ame_sticker:
                    resp["ame_sticker"] = ame_sticker
                self._send_json(resp)
            except Exception as e:
                print(f"  [X] JINE 文字回复失败: {e}")
                self._send_json({"ok": False, "error": str(e)}, status=500)

        else:
            self.send_error(404, "Not Found")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("  + Poketter v2.7.2 -- 场景剥夺JINE + 微信时间线 + 多行输入 + 96px贴图 +")
    print("=" * 50)
    print(f"  地址: http://{HOST}:{PORT}")
    print(f"  API:  GET  /api/timeline  -> 获取时间线")
    print(f"       POST /api/generate   -> 生成新批次")
    print(f"       POST /api/release    -> F7 释放 hidden_pool")
    print(f"       POST /api/jine/send  -> F8 JINE 互动聊天")
    print("=" * 50)

    server = HTTPServer((HOST, PORT), AmechanHandler)
    server.allow_reuse_address = True

    # Start server immediately, generate first batch in background
    import threading
    if feed_count() == 0:
        print("\n[!] Feed 为空，后台生成首条...")
        def _initial_generate():
            try:
                generate_and_save()
                print("  [OK] 首条生成完成")
            except Exception as e:
                print(f"  [!] 生成失败: {e}")
        threading.Thread(target=_initial_generate, daemon=True).start()

    print(f"\n[*] 服务器启动中...\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[~] 超天酱下线~ 明天见!")
        server.shutdown()


if __name__ == "__main__":
    main()
