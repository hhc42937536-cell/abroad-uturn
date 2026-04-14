"""格7：追星行程規劃"""

import json
import os

from bot.constants.cities import IATA_TO_NAME, CITY_FLAG, CITY_CODES
from bot.services.scraper import scrape_idol_events
from bot.services.redis_store import redis_get, redis_set

_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
_cache = {}


def _load_idol_data() -> dict:
    if "idol" in _cache:
        return _cache["idol"]
    try:
        with open(os.path.join(_data_dir, "idol_events.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["idol"] = data
        return data
    except Exception as e:
        print(f"[idol] Load error: {e}")
        return {}


def handle_idol_trip(text: str, user_id: str = "") -> list:
    """追星行程規劃入口"""
    clean = text.replace("\u8ffd\u661f", "").replace("\u884c\u7a0b", "").replace("\u898f\u5283", "").strip()

    if not clean:
        return _show_idol_menu()

    # 搜尋藝人
    data = _load_idol_data()
    all_groups = []
    for country_groups in data.get("groups", {}).values():
        all_groups.extend(country_groups)

    # 模糊匹配
    matched = None
    for group in all_groups:
        if clean.lower() in group["name"].lower() or group["name"].lower() in clean.lower():
            matched = group
            break

    if matched:
        return _show_artist_info(matched, data)

    # 沒匹配到，嘗試爬蟲搜尋
    events = scrape_idol_events(clean)
    if events:
        return _show_scraped_events(clean, events)

    return [{
        "type": "text", "text":
            f"\u627e\u4e0d\u5230\u300c{clean}\u300d\u7684\u76f8\u95dc\u6d3b\u52d5\u8cc7\u8a0a\n\n"
            f"\u8acb\u78ba\u8a8d\u85dd\u4eba/\u5718\u9ad4\u540d\u7a31\uff0c\u6216\u8a66\u8a66\uff1a\n"
            f"\u300c\u8ffd\u661f BTS\u300d\u300c\u8ffd\u661f TWICE\u300d\u300c\u8ffd\u661f Snow Man\u300d",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "BTS", "text": "\u8ffd\u661f BTS"}},
                {"type": "action", "action": {"type": "message", "label": "BLACKPINK", "text": "\u8ffd\u661f BLACKPINK"}},
                {"type": "action", "action": {"type": "message", "label": "\u4e43\u672946", "text": "\u8ffd\u661f \u4e43\u672946"}},
                {"type": "action", "action": {"type": "message", "label": "Snow Man", "text": "\u8ffd\u661f Snow Man"}},
            ],
        },
    }]


def _show_idol_menu() -> list:
    """顯示追星首頁選單（先種草 → 再選藝人）"""
    data = _load_idol_data()
    tips = data.get("tips", [])

    # ── K-POP bubble ──
    kr_groups = data.get("groups", {}).get("KR", [])
    kr_buttons = []
    for g in kr_groups[:6]:
        kr_buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": g["name"][:12], "text": f"\u8ffd\u661f {g['name']}"},
        })
    # K-POP 介紹區
    kr_intro = [
        {"type": "text",
         "text": "\U0001f3ab \u6f14\u5531\u6703 \u30fb \u898f\u5283 \u30fb \u5468\u908a\u5546\u5e97",
         "size": "xs", "color": "#FFFFFF99", "margin": "xs"},
    ]

    # ── J-POP bubble ──
    jp_groups = data.get("groups", {}).get("JP", [])
    jp_buttons = []
    for g in jp_groups[:6]:
        jp_buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": g["name"][:12], "text": f"\u8ffd\u661f {g['name']}"},
        })

    # ── 追星小知識 bubble ──
    tip_lines = []
    for t in tips[:4]:
        tip_lines.append({
            "type": "box", "layout": "horizontal", "margin": "sm",
            "contents": [
                {"type": "text", "text": "\U0001f4a1", "size": "sm", "flex": 1},
                {"type": "text", "text": t, "size": "xs", "color": "#555555",
                 "flex": 11, "wrap": True},
            ],
        })

    bubbles = [
        # K-POP
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E63", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f1f0\U0001f1f7 K-POP \u97d3\u570b\u5076\u50cf",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "\u9ede\u9078\u4f60\u559c\u6b61\u7684\u5718\u9ad4",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": kr_buttons,
            },
        },
        # J-POP
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#FF5722", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f1ef\U0001f1f5 J-POP \u65e5\u672c\u5076\u50cf",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "\u9ede\u9078\u4f60\u559c\u6b61\u7684\u85dd\u4eba",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": jp_buttons,
            },
        },
        # 追星小知識
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#6A1B9A", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f4a1 \u8ffd\u661f\u5c0f\u77e5\u8b58",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "\u51fa\u767c\u524d\u5fc5\u9808\u77e5\u9053\u7684\u4e8b",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "xs", "paddingAll": "12px",
                "contents": tip_lines if tip_lines else [
                    {"type": "text", "text": "\u62b1\u6b49\uff0c\u76ee\u524d\u6c92\u6709\u8cc7\u6599",
                     "size": "sm", "color": "#888888"},
                ],
            },
        },
        # 搜尋其他
        {
            "type": "bubble", "size": "kilo",
            "body": {
                "type": "box", "layout": "vertical",
                "justifyContent": "center", "alignItems": "center",
                "paddingAll": "20px", "spacing": "md",
                "contents": [
                    {"type": "text", "text": "\U0001f50d", "size": "3xl", "align": "center"},
                    {"type": "text", "text": "\u641c\u5c0b\u5176\u4ed6\u85dd\u4eba",
                     "weight": "bold", "size": "md", "align": "center"},
                    {"type": "text",
                     "text": "\u76f4\u63a5\u8f38\u5165\u85dd\u4eba\u540d\u7a31\uff0c\u4f8b\u5982\uff1a\n\u300c\u8ffd\u661f IVE\u300d",
                     "size": "sm", "color": "#888888", "align": "center", "wrap": True},
                ],
            },
        },
    ]

    return [
        {
            "type": "flex",
            "altText": "\u2b50 \u8ffd\u661f\u884c\u7a0b\u898f\u5283",
            "contents": {"type": "carousel", "contents": bubbles},
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "BTS", "text": "\u8ffd\u661f BTS"}},
                    {"type": "action", "action": {"type": "message", "label": "BLACKPINK", "text": "\u8ffd\u661f BLACKPINK"}},
                    {"type": "action", "action": {"type": "message", "label": "TWICE", "text": "\u8ffd\u661f TWICE"}},
                    {"type": "action", "action": {"type": "message", "label": "aespa", "text": "\u8ffd\u661f aespa"}},
                    {"type": "action", "action": {"type": "message", "label": "\u4e43\u672946", "text": "\u8ffd\u661f \u4e43\u672946"}},
                    {"type": "action", "action": {"type": "message", "label": "Snow Man", "text": "\u8ffd\u661f Snow Man"}},
                ],
            },
        },
    ]


def _show_artist_info(artist: dict, data: dict) -> list:
    """顯示藝人資訊 + 場館 + 周邊商店"""
    name = artist["name"]
    agency = artist.get("agency", "")
    genre = artist.get("genre", "")

    # 判斷國家
    country = ""
    for cc, groups in data.get("groups", {}).items():
        if artist in groups:
            country = cc
            break

    bubbles = []

    # Bubble 1: 藝人資訊 + 活動搜尋
    body_text = f"\U0001f3b5 {name}\n\U0001f3e2 \u7d93\u7d00\u516c\u53f8\uff1a{agency}\n\U0001f3b6 \u985e\u578b\uff1a{genre}"

    # 嘗試爬蟲抓活動
    events = scrape_idol_events(name, country)
    if events:
        body_text += "\n\n\U0001f4c5 \u8fd1\u671f\u6d3b\u52d5\uff1a"
        for evt in events[:3]:
            body_text += f"\n\u2022 {evt['date']} {evt.get('venue', '')} ({evt.get('city', '')})"

    bubbles.append({
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#E91E63", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"\u2b50 {name}",
                 "color": "#FFFFFF", "weight": "bold", "size": "lg"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": body_text, "size": "sm", "color": "#444444", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "10px",
            "contents": [
                {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                 "action": {"type": "message", "label": f"\u2708\ufe0f \u898f\u5283\u8ffd\u661f\u65c5\u7a0b",
                            "text": "\u958b\u59cb\u898f\u5283"}},
            ],
        },
    })

    # Bubble 2: 場館資訊
    venues = data.get("venues", {}).get(country, [])
    if venues:
        venue_lines = []
        for v in venues[:5]:
            venue_lines.append(f"\U0001f3df\ufe0f {v['name']}")
            venue_lines.append(f"   \U0001f4cd {v['city']} \u2022 {v.get('capacity', '')} \u4eba")
            venue_lines.append(f"   \U0001f689 {v.get('nearest_station', '')}")
            venue_lines.append("")

        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#1565C0", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f3df\ufe0f \u5e38\u898b\u6f14\u51fa\u5834\u9928",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\n".join(venue_lines).strip(),
                     "size": "sm", "color": "#444444", "wrap": True},
                ],
            },
        })

    # Bubble 3: 周邊商店
    fan_shops = data.get("fan_shops", {}).get(country, [])
    if fan_shops:
        shop_lines = []
        for s in fan_shops[:5]:
            shop_lines.append(f"\U0001f6cd\ufe0f {s['name']}")
            shop_lines.append(f"   {s.get('type', '')} \u2022 {s.get('location', '')}")
            shop_lines.append("")

        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#6A1B9A", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f6cd\ufe0f \u5468\u908a\u5546\u5e97",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\n".join(shop_lines).strip(),
                     "size": "sm", "color": "#444444", "wrap": True},
                ],
            },
        })

    return [
        {
            "type": "flex",
            "altText": f"\u2b50 {name} \u8ffd\u661f\u8cc7\u8a0a",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def _show_scraped_events(artist_name: str, events: list) -> list:
    """顯示爬蟲抓到的活動"""
    lines = [f"\U0001f4c5 {artist_name} \u8fd1\u671f\u6d3b\u52d5\uff1a\n"]
    for evt in events[:8]:
        lines.append(f"\u2022 {evt['date']} | {evt.get('venue', 'TBA')}")
        if evt.get("city"):
            lines[-1] += f" ({evt['city']})"
        if evt.get("url"):
            lines.append(f"   \U0001f517 {evt['url']}")
        lines.append("")

    lines.append("\u8f38\u5165\u300c\u958b\u59cb\u898f\u5283\u300d\u53ef\u4ee5\u76f4\u63a5\u898f\u5283\u8ffd\u661f\u65c5\u7a0b\uff01")

    return [{"type": "text", "text": "\n".join(lines)}]
