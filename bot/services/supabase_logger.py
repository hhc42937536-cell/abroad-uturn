"""Supabase 行為紀錄器（非同步，失敗靜默）"""

import hashlib
import json
import os
import threading
import urllib.error
import urllib.request
from typing import Any


def _uid_hash(user_id: str) -> str:
    """不儲存原始 UID，只存 SHA-256 前 16 字元。"""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def _insert(payload: dict) -> None:
    """向 Supabase REST API 插入一筆紀錄，失敗靜默。"""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        return
    endpoint = f"{url.rstrip('/')}/rest/v1/abroad_events"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception as e:
        print(f"[supabase] {e}")


def log(
    user_id: str,
    event: str,
    *,
    destination: str = "",
    intent: str = "",
    step: int | None = None,
    gather_turns: int | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    非同步寫入 Supabase，不阻塞 webhook 回應。

    事件名稱慣例：
    - trip_start        開始規劃行程
    - trip_complete     完成資訊蒐集，進入航班搜尋
    - plan_generated    計劃書產出
    - llm_gather_ok     LLM gather 成功
    - llm_gather_fail   LLM gather 超時或失敗（fallback）
    - date_parsed_ok    日期解析成功
    - dest_parsed_ok    目的地解析成功
    - dest_parsed_llm   目的地靠 LLM 補救
    """
    payload: dict[str, Any] = {
        "uid_hash": _uid_hash(user_id),
        "event": event,
    }
    if destination:
        payload["destination"] = destination
    if intent:
        payload["intent"] = intent
    if step is not None:
        payload["step"] = step
    if gather_turns is not None:
        payload["gather_turns"] = gather_turns
    if extra:
        payload["extra"] = extra

    threading.Thread(target=_insert, args=(payload,), daemon=True).start()
