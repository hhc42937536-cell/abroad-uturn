"""格3：我的旅行計畫（查看/繼續未完成/歷史計畫）"""

import json
from bot.session.manager import get_session, get_step
from bot.services.redis_store import redis_get, redis_keys
from bot.constants.cities import IATA_TO_NAME, CITY_FLAG


def handle_my_plans(user_id: str) -> list:
    """顯示使用者的旅行計畫（進行中 + 已完成）"""
    step = get_step(user_id)
    session = get_session(user_id)

    messages = []

    # 1. 進行中的計畫
    if step > 0 and session:
        city = session.get("destination_name", "")
        flag = CITY_FLAG.get(session.get("destination_code", ""), "\u2708\ufe0f")
        date_display = session.get("depart_date", "\u672a\u8a2d\u5b9a")
        step_labels = ["", "\u76ee\u7684\u5730", "\u65e5\u671f", "\u4eba\u6578\u9810\u7b97", "\u6a5f\u7968", "\u4f4f\u5bbf", "\u884c\u7a0b", "\u884c\u524d\u9808\u77e5", "\u8a08\u756b\u66f8"]
        current_label = step_labels[step] if step < len(step_labels) else ""

        messages.append({
            "type": "flex",
            "altText": "\u9032\u884c\u4e2d\u7684\u65c5\u884c\u898f\u5283",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "\U0001f4cb \u6211\u7684\u65c5\u884c\u8a08\u756b",
                         "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "md", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "\U0001f6a7 \u9032\u884c\u4e2d\u7684\u898f\u5283", "weight": "bold", "size": "md"},
                        {"type": "separator"},
                        {"type": "text", "text":
                            f"{flag} \u76ee\u7684\u5730\uff1a{city or '\u5c1a\u672a\u9078\u64c7'}\n"
                            f"\U0001f4c5 \u65e5\u671f\uff1a{date_display}\n"
                            f"\U0001f4cd \u76ee\u524d\u9032\u5ea6\uff1a[{step}/8] {current_label}",
                         "size": "sm", "color": "#555555", "wrap": True},
                    ],
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "10px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#FF6B35", "height": "sm",
                         "action": {"type": "message", "label": "\u25b6\ufe0f \u7e7c\u7e8c\u898f\u5283", "text": "\u7e7c\u7e8c\u898f\u5283"}},
                        {"type": "button", "style": "secondary", "height": "sm",
                         "action": {"type": "message", "label": "\U0001f5d1\ufe0f \u53d6\u6d88\u9019\u6b21\u898f\u5283", "text": "\u53d6\u6d88\u898f\u5283"}},
                    ],
                },
            },
        })
    else:
        messages.append({
            "type": "flex",
            "altText": "\U0001f4cb \u6211\u7684\u65c5\u884c\u8a08\u756b",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "18px",
                    "contents": [
                        {"type": "text", "text": "\U0001f4cb \u6211\u7684\u65c5\u884c\u8a08\u756b",
                         "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "\u67e5\u770b\u8a08\u756b \u30fb \u7e7c\u7e8c\u672a\u5b8c\u6210\u7684\u65c5\u7a0b",
                         "color": "#FFE0CC", "size": "sm", "margin": "sm"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "md", "paddingAll": "18px",
                    "contents": [
                        {"type": "text", "text": "\U0001f4ed \u76ee\u524d\u6c92\u6709\u9032\u884c\u4e2d\u7684\u898f\u5283",
                         "weight": "bold", "size": "md", "color": "#555555"},
                        {"type": "separator"},
                        {"type": "text",
                         "text": "\u60f3\u51fa\u570b\u73a9\uff1f\u9078\u4e00\u500b\u65b9\u5f0f\u958b\u59cb\u5427\uff01",
                         "size": "sm", "color": "#888888", "wrap": True},
                        {
                            "type": "box", "layout": "vertical", "spacing": "sm",
                            "margin": "md",
                            "contents": [
                                {
                                    "type": "box", "layout": "horizontal",
                                    "spacing": "sm",
                                    "contents": [
                                        {
                                            "type": "button", "style": "primary",
                                            "color": "#FF6B35", "height": "sm", "flex": 1,
                                            "action": {"type": "message",
                                                       "label": "\u2728 \u5b8c\u6574\u898f\u5283",
                                                       "text": "\u958b\u59cb\u898f\u5283"},
                                        },
                                        {
                                            "type": "button", "style": "primary",
                                            "color": "#E91E63", "height": "sm", "flex": 1,
                                            "action": {"type": "message",
                                                       "label": "\U0001f680 \u8aaa\u8d70\u5c31\u8d70",
                                                       "text": "\u8aaa\u8d70\u5c31\u8d70"},
                                        },
                                    ],
                                },
                                {
                                    "type": "button", "style": "secondary", "height": "sm",
                                    "action": {"type": "message",
                                               "label": "\U0001f30d \u63a2\u7d22\u6700\u4fbf\u5b9c\u76ee\u7684\u5730",
                                               "text": "\u4fbf\u5b9c"},
                                },
                            ],
                        },
                    ],
                },
            },
        })

    # 2. 價格追蹤（作為旅行相關記錄）
    track_keys = redis_keys(f"track:{user_id}:*") if user_id else []
    if track_keys:
        lines = ["\n\U0001f514 \u4f60\u7684\u50f9\u683c\u8ffd\u8e64\uff1a"]
        for key in track_keys[:5]:
            data = redis_get(key)
            if data:
                try:
                    info = json.loads(data)
                    dest_name = IATA_TO_NAME.get(info["destination"], info["destination"])
                    lines.append(f"  \u2022 {dest_name} ({info['depart']})")
                except Exception:
                    pass
        if len(lines) > 1:
            messages.append({"type": "text", "text": "\n".join(lines)})

    return messages
