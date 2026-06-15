"""
推文存储模块 v4 — 完全无状态。
所有数据由前端 localStorage 管理，后端只做无状态计算。
保留此文件仅为兼容 import 路径。
"""
import time
from config import MAX_FEED_ITEMS


# ============================================================
# 仅保留向后兼容的存根（所有返回值来自前端参数，不读文件）
# ============================================================

def pool_count() -> int:
    """已弃用。前端自行管理 pool。"""
    return 0


def feed_count() -> int:
    """已弃用。前端自行管理 timeline。"""
    return 0


def get_timeline(limit: int = 50) -> list[dict]:
    """已弃用。返回空列表。"""
    return []


def get_feed(limit: int = MAX_FEED_ITEMS) -> list[dict]:
    """已弃用。"""
    return []


def get_jine_chat(limit: int = 30) -> list[dict]:
    """已弃用。前端自行管理 JINE 历史。"""
    return []


def clear_feed() -> None:
    """已弃用。无操作。"""
    pass


def save_jine_message(**kwargs) -> dict:
    """已弃用。返回空字典保持兼容。"""
    return {"time": time.strftime("%H:%M"), "reply": ""}
