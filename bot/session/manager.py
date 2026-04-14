"""Session 狀態管理（Redis-backed）"""

import json
import time

from bot.services.redis_store import redis_get, redis_set, redis_del

SESSION_TTL = 86400  # 24 小時


def get_session(user_id: str) -> dict | None:
    """取得使用者的規劃 session"""
    raw = redis_get(f"planning:{user_id}:data")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def get_step(user_id: str) -> int:
    """取得目前步驟（0 表示無 session）"""
    raw = redis_get(f"planning:{user_id}:step")
    if raw is None:
        return 0
    try:
        return int(raw)
    except (ValueError, TypeError):
        return 0


def set_session(user_id: str, data: dict, step: int = None):
    """儲存 session 資料"""
    data["updated_at"] = time.strftime("%Y-%m-%d %H:%M")
    redis_set(f"planning:{user_id}:data", json.dumps(data, ensure_ascii=False), ttl=SESSION_TTL)
    if step is not None:
        redis_set(f"planning:{user_id}:step", str(step), ttl=SESSION_TTL)


def update_session(user_id: str, updates: dict, step: int = None):
    """更新 session 部分欄位"""
    data = get_session(user_id) or {}
    data.update(updates)
    set_session(user_id, data, step=step)


def clear_session(user_id: str):
    """清除 session"""
    redis_del(f"planning:{user_id}:data")
    redis_del(f"planning:{user_id}:step")


def start_session(user_id: str, origin: str = "TPE") -> dict:
    """建立新的規劃 session"""
    data = {
        "origin": origin,
        "started_at": time.strftime("%Y-%m-%d %H:%M"),
    }
    set_session(user_id, data, step=1)
    return data
