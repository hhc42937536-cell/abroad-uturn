"""Upstash Redis 操作"""

import json
import urllib.request

from bot.config import UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN


def _redis_cmd(cmd: list):
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return None
    try:
        data = json.dumps(cmd).encode("utf-8")
        req = urllib.request.Request(
            UPSTASH_REDIS_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("result")
    except Exception as e:
        print(f"[redis] {e}")
        return None


def redis_set(key: str, value: str, ttl: int = 0):
    if ttl > 0:
        return _redis_cmd(["SET", key, value, "EX", str(ttl)])
    return _redis_cmd(["SET", key, value])


def redis_get(key: str):
    return _redis_cmd(["GET", key])


def redis_keys(pattern: str):
    return _redis_cmd(["KEYS", pattern]) or []


def redis_del(key: str):
    return _redis_cmd(["DEL", key])
