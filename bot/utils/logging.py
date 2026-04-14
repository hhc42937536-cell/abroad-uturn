"""Supabase 使用紀錄"""

import json
import hashlib
import urllib.request

from bot.config import SUPABASE_URL, SUPABASE_KEY


def log_usage(user_id: str, feature: str, sub_action: str = None, is_success: bool = True):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        uid_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        data = {"uid_hash": uid_hash, "feature": feature, "is_success": is_success}
        if sub_action:
            data["sub_action"] = sub_action
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/linebot_usage_logs",
            data=body,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"[log] {e}")
