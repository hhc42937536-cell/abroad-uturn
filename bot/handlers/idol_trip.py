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
    """顯示藝人資訊 + 近期活動 + 周邊商店"""
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

    # Bubble 1: 藝人資訊卡
    body_text = f"\U0001f3e2 {agency}\n\U0001f3b6 {genre}"
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
                 "action": {"type": "message", "label": "\u2708\ufe0f \u898f\u5283\u8ffd\u661f\u65c5\u7a0b",
                            "text": "\u958b\u59cb\u898f\u5283"}},
            ],
        },
    })

    # Bubble 2: 近期活動（爬蟲即時）
    import urllib.parse
    search_name = artist.get("search_name", "")
    events = scrape_idol_events(name, country, search_name=search_name)
    if events:
        event_items = []
        for evt in events[:5]:
            line = f"\U0001f4c5 {evt['date']}"
            if evt.get("venue"):
                line += f"\n   \U0001f3df\ufe0f {evt['venue']}"
            if evt.get("city"):
                line += f"  \U0001f4cd {evt['city']}"
            event_items.append({
                "type": "text", "text": line,
                "size": "sm", "color": "#333333", "wrap": True, "margin": "sm",
            })
        event_body_contents = event_items
        footer_contents = [
            {"type": "button", "style": "link", "height": "sm",
             "action": {"type": "uri", "label": "\U0001f517 \u67e5\u66f4\u591a\u6d3b\u52d5",
                        "uri": f"https://www.bandsintown.com/{urllib.parse.quote(name.lower().replace(' ', '-'))}"}}
        ]
    else:
        slug = urllib.parse.quote(name.lower().replace(" ", "-"))
        event_body_contents = [
            {"type": "text", "text": "\u76ee\u524d\u672a\u67e5\u5230\u8fd1\u671f\u516c\u958b\u6d3b\u52d5",
             "size": "sm", "color": "#888888", "wrap": True},
            {"type": "text", "text": "\u53ef\u81ea\u884c\u81f3\u4ee5\u4e0b\u5e73\u53f0\u67e5\u8a62\uff1a",
             "size": "xs", "color": "#aaaaaa", "margin": "md"},
        ]
        footer_contents = [
            {"type": "button", "style": "link", "height": "sm",
             "action": {"type": "uri", "label": "Bandsintown",
                        "uri": f"https://www.bandsintown.com/{slug}"}},
            {"type": "button", "style": "link", "height": "sm",
             "action": {"type": "uri", "label": "Songkick",
                        "uri": f"https://www.songkick.com/search?query={urllib.parse.quote(name)}"}},
        ]

    bubbles.append({
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1565C0", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"\U0001f4e2 {name} \u8fd1\u671f\u6d3b\u52d5",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "xs",
            "contents": event_body_contents,
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "paddingAll": "8px",
            "contents": footer_contents,
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
    """顯示爬蟲抓到的活動（Flex Bubble，與 _show_artist_info 同格式）"""
    import urllib.parse
    slug = urllib.parse.quote(artist_name.lower().replace(" ", "-"))

    event_items = []
    for evt in events[:5]:
        line = f"\U0001f4c5 {evt['date']}"
        if evt.get("venue"):
            line += f"\n   \U0001f3df\ufe0f {evt['venue']}"
        if evt.get("city"):
            line += f"  \U0001f4cd {evt['city']}"
        event_items.append({
            "type": "text", "text": line,
            "size": "sm", "color": "#333333", "wrap": True, "margin": "sm",
        })

    bubble = {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1565C0", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"\U0001f4e2 {artist_name} \u8fd1\u671f\u6d3b\u52d5",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "xs",
            "contents": event_items,
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "paddingAll": "8px",
            "contents": [
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "uri", "label": "\U0001f517 \u67e5\u66f4\u591a\u6d3b\u52d5",
                            "uri": f"https://www.bandsintown.com/{slug}"}},
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "message", "label": "\u2708\ufe0f \u898f\u5283\u8ffd\u661f\u65c5\u7a0b",
                            "text": "\u958b\u59cb\u898f\u5283"}},
            ],
        },
    }

    return [
        {"type": "flex", "altText": f"\U0001f4e2 {artist_name} \u8fd1\u671f\u6d3b\u52d5",
         "contents": bubble},
    ]
