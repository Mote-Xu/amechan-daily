"""
推文存储模块 — JSON 文件持久化
"""
import json
import time
from pathlib import Path
from config import FEED_FILE, DATA_DIR, MAX_FEED_ITEMS


def _ensure_data_dir() -> None:
    """确保 data 目录存在。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_feed_file() -> None:
    """确保 feed.json 存在且为合法 JSON 数组。"""
    _ensure_data_dir()
    if not FEED_FILE.exists():
        _save_raw([])


def _load_raw() -> list[dict]:
    """加载原始 JSON 数据。"""
    _ensure_feed_file()
    try:
        with open(FEED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_raw(data: list[dict]) -> None:
    """保存原始 JSON 数据。"""
    _ensure_data_dir()
    with open(FEED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_feed(limit: int = MAX_FEED_ITEMS) -> list[dict]:
    """加载历史推文列表，最新在前。"""
    data = _load_raw()
    # 按时间戳降序排列
    data.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return data[:limit]


def save_tweet_pair(kangel: str, ame: str, topic: str) -> dict:
    """保存一对推文，返回保存的条目。"""
    entry = {
        "id": f"tweet_{int(time.time() * 1000)}",
        "kangel": kangel,
        "ame": ame,
        "topic": topic,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    data = _load_raw()
    data.append(entry)

    # 截断超出部分
    if len(data) > MAX_FEED_ITEMS:
        data.sort(key=lambda x: x.get("timestamp", 0))
        data = data[-MAX_FEED_ITEMS:]

    _save_raw(data)
    return entry


def get_feed(limit: int = MAX_FEED_ITEMS) -> list[dict]:
    """获取最近 N 条推文，最新在前。"""
    return load_feed(limit)


def clear_feed() -> None:
    """清空所有推文。"""
    _save_raw([])


def feed_count() -> int:
    """返回当前推文总数。"""
    return len(_load_raw())
