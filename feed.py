"""
推文存储模块 v2.7.1 — 时间线 + hidden_pool配对释放 + JINE 互动聊天
"""
import json
import random
import time
from pathlib import Path
from config import FEED_FILE, DATA_DIR, MAX_FEED_ITEMS


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_feed_file() -> None:
    _ensure_data_dir()
    if not FEED_FILE.exists():
        _save_raw({"timeline": [], "hidden_pool": [], "jine_chat": []})


def _load_raw() -> dict:
    _ensure_feed_file()
    try:
        with open(FEED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"timeline": [], "hidden_pool": [], "jine_chat": []}
            data.setdefault("timeline", [])
            data.setdefault("hidden_pool", [])
            data.setdefault("jine_chat", [])
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return {"timeline": [], "hidden_pool": [], "jine_chat": []}


def _save_raw(data: dict) -> None:
    _ensure_data_dir()
    with open(FEED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_timeline(items: list[dict], event: str) -> int:
    batch_id = f"batch_{int(time.time() * 1000)}"
    data = _load_raw()
    for item in items:
        entry = {
            "batch_id": batch_id, "event": event,
            "layer": item.get("layer", "poketter"),
            "time": item.get("time", ""), "text": item.get("text", ""),
            "type": item.get("type", "text"),
            "selfie_mood": item.get("selfie_mood", "angel"),
            "timestamp": time.time(), "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["timeline"].append(entry)
    batches = list(dict.fromkeys([e.get("batch_id") for e in data["timeline"]]))
    if len(batches) > 10:
        cutoff = batches[-10]
        data["timeline"] = [e for e in data["timeline"] if e.get("batch_id") >= cutoff]
    _save_raw(data)
    return len(items)


def get_timeline(limit: int = 50) -> list[dict]:
    data = _load_raw()
    timeline = data.get("timeline", [])
    timeline.sort(key=lambda x: (x.get("batch_id", ""), x.get("time", "")), reverse=True)
    return timeline[:limit]


def save_hidden_pool(items: list[dict]) -> int:
    data = _load_raw()
    pool = [{"layer": it.get("layer", "poketter"), "text": it.get("text", ""),
             "selfie_mood": it.get("selfie_mood", "angel")} for it in items]
    data["hidden_pool"] = pool
    _save_raw(data)
    return len(pool)


def pop_from_pool() -> list[dict]:
    """释放一对：Poketter + Diary。返回 1-2 条。"""
    data = _load_raw()
    pool = data.get("hidden_pool", [])
    if not pool:
        return []
    entries = []
    batch_id = f"released_{int(time.time() * 1000)}"

    def _pop_one(layer: str) -> dict | None:
        for i, it in enumerate(pool):
            if it.get("layer") == layer:
                item = pool.pop(i)
                entry = {
                    "batch_id": batch_id, "event": "随手一发",
                    "layer": item.get("layer", layer),
                    "time": time.strftime("%H:%M"), "text": item.get("text", ""),
                    "selfie_mood": item.get("selfie_mood", "angel"),
                    "timestamp": time.time(), "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                data["timeline"].append(entry)
                return entry
        return None

    poke = _pop_one("poketter")
    if poke: entries.append(poke)
    diary = _pop_one("diary")
    if diary: entries.append(diary)
    if not entries and pool:
        item = pool.pop(0)
        entry = {
            "batch_id": batch_id, "event": "随手一发",
            "layer": item.get("layer", "poketter"),
            "time": time.strftime("%H:%M"), "text": item.get("text", ""),
            "selfie_mood": item.get("selfie_mood", "angel"),
            "timestamp": time.time(), "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["timeline"].append(entry)
        entries.append(entry)
    data["hidden_pool"] = pool
    _save_raw(data)
    return entries


def pool_count() -> int:
    return len(_load_raw().get("hidden_pool", []))


def save_tweet_pair(kangel: str, ame: str, topic: str) -> dict:
    items = [
        {"layer": "poketter", "time": time.strftime("%H:%M"), "text": kangel, "selfie_mood": "angel"},
        {"layer": "diary", "time": time.strftime("%H:%M"), "text": ame, "selfie_mood": "home"},
    ]
    save_timeline(items, topic)
    return {"kangel": kangel, "ame": ame, "topic": topic}


def get_feed(limit: int = MAX_FEED_ITEMS) -> list[dict]:
    return get_timeline(limit)


def clear_feed() -> None:
    _save_raw({"timeline": [], "hidden_pool": [], "jine_chat": []})


def feed_count() -> int:
    return len(_load_raw().get("timeline", []))


def save_jine_message(sticker: str = "", reply: str = "", ame_sticker: str | None = None,
                      player_text: str = "") -> dict:
    data = _load_raw()
    data.setdefault("jine_chat", [])
    t = time.strftime("%H:%M")
    msg = {"time": t, "reply": reply, "timestamp": time.time()}
    if sticker: msg["sticker"] = sticker
    if player_text: msg["player_text"] = player_text
    if ame_sticker: msg["ame_sticker"] = ame_sticker
    if random.random() < 0.2 and len(reply) > 3 and not ame_sticker:
        msg["recall"] = True
    data["jine_chat"].append(msg)
    if len(data["jine_chat"]) > 30:
        data["jine_chat"] = data["jine_chat"][-30:]
    _save_raw(data)
    return msg


def get_jine_chat(limit: int = 30) -> list[dict]:
    return _load_raw().get("jine_chat", [])[-limit:]
