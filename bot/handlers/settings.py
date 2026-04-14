"""出發地設定 + 使用者偏好"""

from bot.constants.cities import TW_AIRPORTS
from bot.services.redis_store import redis_get, redis_set


def get_user_origin(user_id: str) -> str:
    """取得使用者設定的出發地（預設 TPE）"""
    from bot.config import UPSTASH_REDIS_URL
    if not UPSTASH_REDIS_URL or not user_id:
        return "TPE"
    origin = redis_get(f"origin:{user_id}")
    return origin if origin else "TPE"


def handle_set_origin(user_id: str, text: str) -> list:
    """設定出發機場"""
    from bot.config import UPSTASH_REDIS_URL
    city = text.replace("出發地", "").replace("設定", "").replace("改", "").strip()

    if not city:
        current = get_user_origin(user_id)
        current_name = {v: k for k, v in TW_AIRPORTS.items()}.get(current, current)
        buttons = []
        for name, code in [("台北 桃園", "TPE"), ("高雄 小港", "KHH"), ("台中 清泉崗", "RMQ"), ("台南", "TNN")]:
            marker = " \u2705" if code == current else ""
            buttons.append({
                "type": "button",
                "style": "primary" if code == current else "secondary",
                "height": "sm",
                "action": {"type": "message", "label": f"{name}{marker}", "text": f"\u51fa\u767c\u5730 {name.split()[0]}"},
            })
        return [{
            "type": "flex",
            "altText": "\u8a2d\u5b9a\u51fa\u767c\u6a5f\u5834",
            "contents": {
                "type": "bubble", "size": "kilo",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "\U0001f6eb \u8a2d\u5b9a\u51fa\u767c\u6a5f\u5834",
                         "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                        {"type": "text", "text": f"\u76ee\u524d\uff1a{current_name} ({current})",
                         "color": "#FFE0CC", "size": "sm"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": buttons,
                },
            },
        }]

    code = TW_AIRPORTS.get(city)
    if not code:
        return [{"type": "text", "text":
            f"\u627e\u4e0d\u5230\u300c{city}\u300d\u7684\u6a5f\u5834\n\n"
            f"\u652f\u63f4\u7684\u51fa\u767c\u5730\uff1a\u53f0\u5317\u3001\u9ad8\u96c4\u3001\u53f0\u4e2d\u3001\u53f0\u5357\n"
            f"\u4f8b\u5982\uff1a\u300c\u51fa\u767c\u5730 \u9ad8\u96c4\u300d"
        }]

    if UPSTASH_REDIS_URL and user_id:
        redis_set(f"origin:{user_id}", code, ttl=86400 * 365)

    city_name = {v: k for k, v in TW_AIRPORTS.items()}.get(code, city)
    return [{"type": "text", "text":
        f"\u2705 \u51fa\u767c\u5730\u5df2\u8a2d\u5b9a\u70ba\uff1a{city} ({code})\n\n"
        f"\u4ee5\u5f8c\u641c\u5c0b\u90fd\u6703\u5f9e {code} \u51fa\u767c\uff01\n"
        f"\u8f38\u5165\u300c\u4fbf\u5b9c\u300d\u8a66\u8a66\u770b \u2708\ufe0f"
    }]
