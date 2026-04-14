"""LINE Messaging API 工具"""

import json
import hashlib
import hmac
import urllib.request

from bot.config import CHANNEL_SECRET, CHANNEL_ACCESS_TOKEN


def reply_message(reply_token, messages):
    if not messages:
        return
    if not CHANNEL_ACCESS_TOKEN or not reply_token:
        print(f"[reply] SKIPPED: token={'empty' if not reply_token else 'ok'}")
        return
    data = json.dumps({
        "replyToken": reply_token,
        "messages": messages[:5],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/reply",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[reply] SUCCESS: {resp.status}")
    except Exception as e:
        print(f"[reply] ERROR: {e}")
        if hasattr(e, 'read'):
            print(f"[reply] BODY: {e.read().decode('utf-8', 'ignore')}")


def push_message(user_id: str, messages: list):
    if not messages or not user_id or not CHANNEL_ACCESS_TOKEN:
        return
    data = json.dumps({
        "to": user_id,
        "messages": messages[:5],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[push] SUCCESS: {resp.status}")
    except Exception as e:
        print(f"[push] ERROR: {e}")
        if hasattr(e, 'read'):
            print(f"[push] BODY: {e.read().decode('utf-8', 'ignore')}")


def verify_signature(body: bytes, signature: str) -> bool:
    if not CHANNEL_SECRET:
        return True
    mac = hmac.new(CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256)
    import base64
    return hmac.compare_digest(base64.b64encode(mac.digest()).decode("utf-8"), signature)
