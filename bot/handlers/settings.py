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
        options = [
            ("桃園國際機場 TPE", "TPE", "桃園"),
            ("台北松山機場 TSA", "TSA", "松山"),
            ("高雄國際機場 KHH", "KHH", "高雄"),
            ("台中清泉崗機場 RMQ", "RMQ", "台中"),
            ("台南機場 TNN", "TNN", "台南"),
        ]
        buttons = []
        for label, code, trigger in options:
            marker = " ✅" if code == current else ""
            buttons.append({
                "type": "button",
                "style": "primary" if code == current else "secondary",
                "height": "sm",
                "action": {"type": "message", "label": f"{label}{marker}", "text": f"出發地 {trigger}"},
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
            f"找不到「{city}」的機場\n\n"
            f"支援的出發地：桃園、松山、高雄、台中、台南\n"
            f"例如：「出發地 高雄」"
        }]

    if UPSTASH_REDIS_URL and user_id:
        redis_set(f"origin:{user_id}", code, ttl=86400 * 365)

    city_name = {v: k for k, v in TW_AIRPORTS.items()}.get(code, city)
    return [{"type": "text", "text":
        f"\u2705 \u51fa\u767c\u5730\u5df2\u8a2d\u5b9a\u70ba\uff1a{city} ({code})\n\n"
        f"\u4ee5\u5f8c\u641c\u5c0b\u90fd\u6703\u5f9e {code} \u51fa\u767c\uff01\n"
        f"\u8f38\u5165\u300c\u4fbf\u5b9c\u300d\u8a66\u8a66\u770b \u2708\ufe0f"
    }]
