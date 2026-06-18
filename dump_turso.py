"""从 Turso 拉取存档内容用于质量审查。Token 从 .env 读取。"""
import json, urllib.request, sys, os
sys.stdout.reconfigure(encoding="utf-8")

# 读 .env
env = {}
with open(os.path.join(os.path.dirname(__file__), ".env")) as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            env[k] = v

if "TURSO_URL" not in env:
    print("请在 .env 中设置 TURSO_URL + TURSO_TOKEN")
    sys.exit(1)

URL = env["TURSO_URL"].replace("libsql://", "https://") + "/v2/pipeline"
TOKEN = env["TURSO_TOKEN"]

def query(sql, args=None):
    stmt = {"sql": sql}
    if args: stmt["args"] = [{"type": "text", "value": str(v)} for v in args]
    body = json.dumps({"requests": [{"type": "execute", "stmt": stmt}]}).encode()
    req = urllib.request.Request(URL, data=body,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        rows = json.loads(r.read())["results"][0].get("response", {}).get("result", {}).get("rows", [])
    return [[c["value"] for c in row] for row in rows]

rows = query("SELECT user_id, slot_id, updated_at, save_data FROM user_game_saves ORDER BY updated_at DESC")
print(f"=== {len(rows)} saves ===\n")

for uid, sid, ts, data_str in rows[:5]:
    data = json.loads(data_str)
    name = data.get("name", "?")
    print(f"## {name} ({sid[:20]}...) | {ts} | uid:{uid[:8]}")

    timeline = data.get("timeline", [])
    if timeline:
        print(f"推博 ({len(timeline)}):")
        for t in timeline[-6:]:
            tag = "💖" if t.get("layer") == "poketter" else "💊"
            print(f"  {tag} {t.get('text','')[:80]}")

    chat = data.get("jineChat", [])
    if chat:
        print(f"JINE ({len(chat)}):")
        for m in chat[-10:]:
            if m.get("player_text"): print(f"  P: {m['player_text'][:60]}")
            if m.get("sticker"):     print(f"  P: [{m['sticker']}]")
            if m.get("reply"):       print(f"  糖糖: {m['reply'][:80]}")
    print()
