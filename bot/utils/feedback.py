"""行程滿意度回饋：回程後 D+1 推送問卷"""

import json
import datetime

from bot.services.redis_store import redis_get, redis_del, redis_keys
from bot.services.line_api import push_message


def _build_feedback_flex(city: str, days: int) -> dict:
    return {
        "type": "flex",
        "altText": f"🌟 {city} 旅行結束了！分享你的感受",
        "contents": {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#FF6B35", "paddingAll": "14px",
                "contents": [
                    {"type": "text", "text": "🌟 旅行結束了！",
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": f"{city} {days}天 — 怎麼樣？",
                     "color": "#FFE0CC", "size": "sm", "margin": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "14px", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "幫我打個分吧 😊",
                     "weight": "bold", "size": "md"},
                    {"type": "text", "text": "你的回饋讓出國優轉變得更好！",
                     "size": "xs", "color": "#999999", "margin": "xs"},
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "paddingAll": "10px", "spacing": "sm",
                "contents": [
                    {
                        "type": "box", "layout": "horizontal", "spacing": "sm",
                        "contents": [
                            {"type": "button", "style": "secondary", "height": "sm", "flex": 1,
                             "action": {"type": "postback", "label": "⭐⭐⭐⭐⭐", "data": "feedback:5"}},
                            {"type": "button", "style": "secondary", "height": "sm", "flex": 1,
                             "action": {"type": "postback", "label": "⭐⭐⭐⭐", "data": "feedback:4"}},
                        ],
                    },
                    {
                        "type": "box", "layout": "horizontal", "spacing": "sm",
                        "contents": [
                            {"type": "button", "style": "secondary", "height": "sm", "flex": 1,
                             "action": {"type": "postback", "label": "⭐⭐⭐", "data": "feedback:3"}},
                            {"type": "button", "style": "secondary", "height": "sm", "flex": 1,
                             "action": {"type": "postback", "label": "⭐⭐", "data": "feedback:2"}},
                            {"type": "button", "style": "secondary", "height": "sm", "flex": 1,
                             "action": {"type": "postback", "label": "⭐", "data": "feedback:1"}},
                        ],
                    },
                ],
            },
        },
    }


def check_and_send_feedback() -> dict:
    """Cron: 每天 09:00 檢查是否有需要發送的滿意度問卷"""
    today = datetime.date.today().isoformat()
    sent = 0
    errors = 0

    try:
        keys = redis_keys("feedback:*")
    except Exception:
        return {"status": "error", "message": "redis_keys failed"}

    for key in keys:
        try:
            raw = redis_get(key)
            if not raw:
                continue
            data = json.loads(raw)
            return_date = data.get("return_date", "")
            if not return_date:
                continue

            # 回程隔天才發送
            ret_day = datetime.date.fromisoformat(return_date[:10])
            send_day = ret_day + datetime.timedelta(days=1)
            if send_day.isoformat() != today:
                continue

            # 取得 user_id（key = "feedback:{user_id}"）
            user_id = key.split(":", 1)[1] if ":" in key else None
            if not user_id:
                continue

            city = data.get("city", "旅行")
            days = data.get("days", 0)
            msg = _build_feedback_flex(city, days)
            push_message(user_id, [msg])
            redis_del(key)
            sent += 1
        except Exception:
            errors += 1

    return {"status": "ok", "sent": sent, "errors": errors, "date": today}


def handle_feedback_postback(score: int, user_id: str) -> list:
    """處理用戶回饋評分"""
    stars = "⭐" * score
    if score >= 4:
        reply = f"{stars}\n謝謝你的好評！下次旅行繼續找我 ✈️"
    elif score == 3:
        reply = f"{stars}\n謝謝回饋！有什麼可以改進的地方嗎？\n隨時傳訊息告訴我 😊"
    else:
        reply = f"{stars}\n謝謝你的回饋，我會繼續改進的 🙏\n下次希望能給你更好的體驗！"

    try:
        from bot.services.redis_store import redis_set
        redis_set(f"feedback_score:{user_id}", str(score), ttl=60 * 60 * 24 * 90)
    except Exception:
        pass

    return [{"type": "text", "text": reply}]
