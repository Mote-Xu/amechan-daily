"""
推文存储模块 v2 — 时间线 + hidden_pool + JINE 互动聊天
v2.8: 水位线自动补池 — 后端后台静默生成，前端 O(1) 释放
"""
import json
import random
import threading
import time
from pathlib import Path
from config import FEED_FILE, DATA_DIR, MAX_FEED_ITEMS

# 全局锁，防止并发生成
_is_generating = False
_WATERLINE = 2  # pool 少于 2 对时触发后台补池


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_feed_file() -> None:
    _ensure_data_dir()
    if not FEED_FILE.exists():
        _save_raw({"timeline": [], "hidden_pool": [], "jine_chat": []})


def _load_raw() -> dict:
    """加载原始数据。返回 dict 含 timeline 和 hidden_pool。"""
    _ensure_feed_file()
    try:
        with open(FEED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"timeline": [], "hidden_pool": []}
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


# ============================================================
# 时间线
# ============================================================

def save_timeline(items: list[dict], event: str) -> int:
    """保存一组时间线条目，返回保存数量。"""
    batch_id = f"batch_{int(time.time() * 1000)}"
    data = _load_raw()

    for item in items:
        entry = {
            "batch_id": batch_id,
            "event": event,
            "layer": item.get("layer", "poketter"),
            "time": item.get("time", ""),
            "text": item.get("text", ""),
            "type": item.get("type", "text"),  # "text" or "system" (JINE recall)
            "selfie_mood": item.get("selfie_mood", "angel"),
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["timeline"].append(entry)

    # 截断旧数据（按 batch 保留最近 10 批）
    batches = list(dict.fromkeys([e.get("batch_id") for e in data["timeline"]]))
    if len(batches) > 10:
        cutoff = batches[-10]
        data["timeline"] = [e for e in data["timeline"] if e.get("batch_id") >= cutoff]

    _save_raw(data)
    return len(items)


def get_timeline(limit: int = 50) -> list[dict]:
    """获取时间线，按时间倒序，再按 batch 分组。"""
    data = _load_raw()
    timeline = data.get("timeline", [])
    timeline.sort(key=lambda x: (x.get("batch_id", ""), x.get("time", "")), reverse=True)
    return timeline[:limit]


# ============================================================
# Hidden Pool（F7 伪生成按钮用）
# ============================================================

def save_hidden_pool(items: list[dict]) -> int:
    """覆盖写入 hidden_pool。"""
    data = _load_raw()
    pool = []
    for item in items:
        pool.append({
            "layer": item.get("layer", "poketter"),
            "text": item.get("text", ""),
            "selfie_mood": item.get("selfie_mood", "angel"),
        })
    data["hidden_pool"] = pool
    _save_raw(data)
    return len(pool)


def pop_from_pool() -> list[dict]:
    """从 hidden_pool 释放一对：一条 Poketter + 一条 Diary。
    返回条目列表（1-2条）。糖糖同时用两个身份发动态——公开的超天酱和私密的自己。"""
    data = _load_raw()
    pool = data.get("hidden_pool", [])
    if not pool:
        return []

    entries = []
    batch_id = f"released_{int(time.time() * 1000)}"

    def _find_one(layer: str) -> dict | None:
        """查找但不移除。返回 pool 中的原始条目。"""
        for it in pool:
            if it.get("layer") == layer:
                return it
        return None

    def _pop_it(item: dict) -> dict:
        """移除并写入 timeline。"""
        pool.remove(item)
        entry = {
            "batch_id": batch_id, "event": "随手一发",
            "layer": item.get("layer", "poketter"),
            "time": time.strftime("%H:%M"), "text": item.get("text", ""),
            "selfie_mood": item.get("selfie_mood", "angel"),
            "timestamp": time.time(), "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        data["timeline"].append(entry)
        return entry

    # Must release as a pair — both must exist
    poke_item = _find_one("poketter")
    diary_item = _find_one("diary")

    if poke_item and diary_item:
        entries.append(_pop_it(poke_item))
        entries.append(_pop_it(diary_item))
        data["hidden_pool"] = pool
        _save_raw(data)
        return entries

    # Incomplete pair → regenerate pool (don't release singles)
    print(f"  [!] Pool imbalanced: poke={bool(poke_item)}, diary={bool(diary_item)} → trigger regeneration")
    return []


def pool_count() -> int:
    """hidden_pool 剩余条数。"""
    return len(_load_raw().get("hidden_pool", []))


# ============================================================
# 旧版兼容
# ============================================================

def save_tweet_pair(kangel: str, ame: str, topic: str) -> dict:
    """旧版：保存一对推文到时间线。"""
    items = [
        {"layer": "poketter", "time": time.strftime("%H:%M"), "text": kangel, "selfie_mood": "angel"},
        {"layer": "diary", "time": time.strftime("%H:%M"), "text": ame, "selfie_mood": "home"},
    ]
    save_timeline(items, topic)
    return {"kangel": kangel, "ame": ame, "topic": topic}


def get_feed(limit: int = MAX_FEED_ITEMS) -> list[dict]:
    """旧版兼容：返回时间线。"""
    return get_timeline(limit)


def clear_feed() -> None:
    """清空所有数据。"""
    _save_raw({"timeline": [], "hidden_pool": [], "jine_chat": []})


def feed_count() -> int:
    """时间线条目总数。"""
    return len(_load_raw().get("timeline", []))


# ============================================================
# JINE 互动聊天 (F8)
# ============================================================

def save_jine_message(sticker: str = "", reply: str = "", ame_sticker: str | None = None, player_text: str = "") -> dict:
    """保存一条互动 JINE 聊天记录。
    sticker: 玩家发的贴图 ID（贴图模式）
    player_text: 玩家发的文字消息（文字模式）
    reply: 糖糖的文字回复
    ame_sticker: 糖糖回复的贴图 ID"""
    data = _load_raw()
    data.setdefault("jine_chat", [])

    t = time.strftime("%H:%M")
    msg = {
        "time": t,
        "reply": reply,
        "timestamp": time.time(),
    }

    if sticker:
        msg["sticker"] = sticker
    if player_text:
        msg["player_text"] = player_text
    if ame_sticker:
        msg["ame_sticker"] = ame_sticker

    if random.random() < 0.2 and len(reply) > 3 and not ame_sticker:
        msg["recall"] = True

    data["jine_chat"].append(msg)

    # 最多保留 30 条聊天记录
    if len(data["jine_chat"]) > 30:
        data["jine_chat"] = data["jine_chat"][-30:]

    _save_raw(data)
    return msg


def get_jine_chat(limit: int = 30) -> list[dict]:
    """获取 JINE 互动聊天历史。"""
    data = _load_raw()
    return data.get("jine_chat", [])[-limit:]

