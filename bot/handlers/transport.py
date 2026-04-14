"""當地交通攻略 — 地鐵卡、路線、App"""

import json
import os

from bot.utils.date_parser import parse_destination
from bot.constants.cities import IATA_TO_COUNTRY

_data_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data"
)
_cache = {}

# IATA → transport key
_IATA_MAP = {
    "TYO": "TYO", "NRT": "TYO", "HND": "TYO",
    "NGO": "TYO", "SPK": "TYO",
    "OSA": "OSA", "KIX": "OSA", "ITM": "OSA", "FUK": "OSA",
    "SEL": "SEL", "ICN": "SEL", "GMP": "SEL",
    "PUS": "SEL",
    "BKK": "BKK", "DMK": "BKK",
    "SIN": "SIN",
    "HKG": "HKG",
    "KUL": "KUL",
    "SGN": "SGN", "HAN": "SGN",
}

_POPULAR = [
    ("TYO", "\U0001f1ef\U0001f1f5", "\u6771\u4eac"),
    ("OSA", "\U0001f1ef\U0001f1f5", "\u5927\u962a"),
    ("SEL", "\U0001f1f0\U0001f1f7", "\u9996\u723e"),
    ("BKK", "\U0001f1f9\U0001f1ed", "\u66fc\u8c37"),
    ("SIN", "\U0001f1f8\U0001f1ec", "\u65b0\u52a0\u5761"),
    ("HKG", "\U0001f1ed\U0001f1f0", "\u9999\u6e2f"),
    ("KUL", "\U0001f1f2\U0001f1fe", "\u5409\u9686\u5761"),
    ("SGN", "\U0001f1fb\U0001f1f3", "\u80e1\u5fd7\u660e"),
]

_NAME_MAP = {
    "\u6771\u4eac": "TYO", "\u65e5\u672c": "TYO", "\u5927\u962a": "OSA",
    "\u6c96\u7e04": "TYO", "\u798f\u5ca1": "OSA", "\u672d\u5e4c": "TYO",
    "\u9996\u723e": "SEL", "\u97d3\u570b": "SEL", "\u91d8\u5c71": "SEL",
    "\u66fc\u8c37": "BKK", "\u6cf0\u570b": "BKK", "\u6e05\u9083": "BKK",
    "\u65b0\u52a0\u5761": "SIN",
    "\u9999\u6e2f": "HKG",
    "\u5409\u9686\u5761": "KUL", "\u99ac\u4f86\u897f\u4e9e": "KUL",
    "\u80e1\u5fd7\u660e": "SGN", "\u8d8a\u5357": "SGN", "\u6cb3\u5167": "SGN",
}


def _load() -> dict:
    if "transport" in _cache:
        return _cache["transport"]
    try:
        with open(os.path.join(_data_dir, "transport_info.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["transport"] = data
        return data
    except Exception as e:
        print(f"[transport] Load error: {e}")
        return {}


def handle_transport(text: str, user_id: str = "") -> list:
    """交通攻略入口"""
    clean = (text
             .replace("\u4ea4\u901a\u653b\u7565", "")
             .replace("\u4ea4\u901a\u5361", "")
             .replace("\u5730\u9435", "")
             .replace("\u635f\u904b", "")
             .replace("\u7b2c\u5361", "")
             .replace("\u666f\u9ede\u5361", "")
             .replace("\u4ea4\u901a", "")
             .strip())

    if not clean:
        return _show_overview()

    # 先試名稱對照
    for name, key in _NAME_MAP.items():
        if name in clean:
            return _show_detail(key)

    # 再試 IATA
    dest = parse_destination(clean)
    if dest:
        key = _IATA_MAP.get(dest)
        if key:
            return _show_detail(key)

    return [{"type": "text",
             "text": f"\u76ee\u524d\u6c92\u6709\u300c{clean}\u300d\u7684\u4ea4\u901a\u653b\u7565\n\n\u53ef\u4ee5\u9ede\u4e0b\u65b9\u57ce\u5e02\u5feb\u901f\u67e5\u8a62"}]


def _show_overview() -> list:
    """入口：熱門城市交通卡一覽"""
    data = _load()
    bubbles = []

    for key, flag, city in _POPULAR:
        info = data.get(key, {})
        if not info:
            continue
        cards = info.get("cards", [])
        tips = info.get("tips", [])
        grab = info.get("grab_available", False)
        taxi_app = info.get("taxi_app", "")

        # 主要交通卡簡介
        card_lines = []
        for c in cards[:2]:
            card_lines.append({
                "type": "box", "layout": "vertical", "margin": "sm",
                "contents": [
                    {"type": "text",
                     "text": f"\U0001f4b3 {c['name']}",
                     "size": "sm", "weight": "bold", "color": "#333333"},
                    {"type": "text",
                     "text": f"  {c.get('deposit','')}  \U0001f4cd{c.get('where_to_buy','')[:20]}",
                     "size": "xxs", "color": "#888888", "wrap": True},
                ],
            })

        if not card_lines:
            card_lines.append({
                "type": "text",
                "text": "\U0001f4f1 \u4e3b\u8981\u4ea4\u901a\uff1aGrab \u53eb\u8eca / \u5730\u9435\u5728\u7dda\u8cfc\u7968",
                "size": "sm", "color": "#555555", "wrap": True,
            })

        # Grab 標籤
        extra = []
        if grab:
            extra.append({"type": "text",
                          "text": "\U0001f7e2 Grab \u53ef\u7528\uff0c\u5f37\u70c8\u63a8\u85a6",
                          "size": "xxs", "color": "#2E7D32"})
        if taxi_app and not grab:
            extra.append({"type": "text",
                          "text": f"\U0001f695 {taxi_app}",
                          "size": "xxs", "color": "#555555"})

        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#1A237E", "paddingAll": "14px",
                "contents": [
                    {"type": "text",
                     "text": f"{flag} {city}",
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                    {"type": "text",
                     "text": "\U0001f687 \u4ea4\u901a\u5361 & \u8def\u7dda",
                     "color": "#9FA8DA", "size": "xs", "margin": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "12px", "spacing": "xs",
                "contents": card_lines + ([{"type": "separator", "margin": "sm"}] if extra else []) + extra,
            },
            "footer": {
                "type": "box", "layout": "vertical", "paddingAll": "10px",
                "contents": [
                    {"type": "button", "style": "primary", "height": "sm",
                     "color": "#1A237E",
                     "action": {"type": "message",
                                "label": f"\U0001f4cd {city}\u5b8c\u6574\u653b\u7565",
                                "text": f"\u4ea4\u901a\u653b\u7565 {city}"}},
                ],
            },
        })

    qr_items = [
        {"type": "action", "action": {"type": "message",
         "label": f"{flag} {city}", "text": f"\u4ea4\u901a\u653b\u7565 {city}"}}
        for _, flag, city in _POPULAR
    ]

    return [
        {"type": "text",
         "text": "\U0001f687 \u5404\u57ce\u5e02\u4ea4\u901a\u653b\u7565\n\u2190 \u5de6\u53f3\u6ed1\u52d5\uff0c\u9ede\u300c\u5b8c\u6574\u653b\u7565\u300d\u770b\u8a73\u7d30"},
        {
            "type": "flex",
            "altText": "\U0001f687 \u5404\u57ce\u5e02\u4ea4\u901a\u653b\u7565",
            "contents": {"type": "carousel", "contents": bubbles},
            "quickReply": {"items": qr_items},
        },
    ]


def _show_detail(city_key: str) -> list:
    """單城市詳細交通攻略"""
    data = _load()
    info = data.get(city_key)
    if not info:
        return [{"type": "text", "text": "\u76ee\u524d\u9084\u6c92\u6709\u9019\u500b\u57ce\u5e02\u7684\u8cc7\u6599"}]

    city = info.get("city_name", city_key)
    flag = info.get("flag", "\U0001f30d")
    cards = info.get("cards", [])
    lines = info.get("metro_lines", [])
    tips = info.get("tips", [])
    grab = info.get("grab_available", False)
    taxi_app = info.get("taxi_app", "")
    key_stations = info.get("key_stations", [])

    bubbles = []

    # Bubble 1: 交通卡詳情
    card_contents = []
    if cards:
        for c in cards:
            card_contents += [
                {"type": "text", "text": f"\U0001f4b3 {c['name']}",
                 "weight": "bold", "size": "sm", "color": "#1A237E", "margin": "md"},
                {"type": "box", "layout": "vertical", "margin": "xs", "spacing": "xs",
                 "contents": [
                     {"type": "text", "text": f"\U0001f3f7\ufe0f \u5361\u8cbb/\u62bc\u91d1\uff1a{c.get('deposit','')}",
                      "size": "xs", "color": "#555555", "wrap": True},
                     {"type": "text", "text": f"\U0001f4cd \u5728\u54ea\u8cb7\uff1a{c.get('where_to_buy','')}",
                      "size": "xs", "color": "#555555", "wrap": True},
                     {"type": "text", "text": f"\U0001f4e1 \u5f91\u6e96\u7bc4\u570d\uff1a{c.get('coverage','')}",
                      "size": "xs", "color": "#555555", "wrap": True},
                     {"type": "text", "text": f"\U0001f4a1 {c.get('tip','')}",
                      "size": "xs", "color": "#E65100", "wrap": True},
                 ]},
                {"type": "separator", "margin": "sm"},
            ]
    else:
        card_contents.append({
            "type": "text",
            "text": "\U0001f4f1 \u6b64\u57ce\u5e02\u4e3b\u8981\u4ea4\u901a\u4ee5 Grab / \u5730\u9435\u5728\u7dda\u8cfc\u7968\u70ba\u4e3b",
            "size": "sm", "color": "#555555", "wrap": True,
        })

    bubbles.append({
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1A237E", "paddingAll": "14px",
            "contents": [
                {"type": "text", "text": f"{flag} {city} \u4ea4\u901a\u5361",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
                {"type": "text", "text": "\u8cb7\u54ea\u5f35\u3001\u7528\u54ea\u88e1",
                 "color": "#9FA8DA", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {"type": "box", "layout": "vertical",
                 "paddingAll": "12px", "spacing": "xs",
                 "contents": card_contents},
    })

    # Bubble 2: 重要路線 + 重點站
    if lines:
        line_contents = [
            {"type": "text", "text": line, "size": "sm",
             "color": "#333333", "wrap": True, "margin": "xs"}
            for line in lines
        ]
        if key_stations:
            line_contents += [
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": "\U0001f4cd \u91cd\u8981\u7ad9",
                 "size": "xs", "color": "#888888", "weight": "bold", "margin": "sm"},
                {"type": "text",
                 "text": "  ".join(key_stations),
                 "size": "xs", "color": "#555555", "wrap": True, "margin": "xs"},
            ]
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#283593", "paddingAll": "14px",
                "contents": [
                    {"type": "text", "text": f"\U0001f687 {city} \u91cd\u8981\u8def\u7dda",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                ],
            },
            "body": {"type": "box", "layout": "vertical",
                     "paddingAll": "12px", "spacing": "xs",
                     "contents": line_contents},
        })

    # Bubble 3: 旅遊小撇步
    if tips:
        tip_contents = [
            {"type": "text", "text": f"\U0001f4a1 {t}",
             "size": "sm", "color": "#444444", "wrap": True, "margin": "sm"}
            for t in tips
        ]
        if grab:
            tip_contents.insert(0, {
                "type": "text",
                "text": "\U0001f7e2 Grab \u53ef\u7528\uff01\u53eb\u8eca\u9996\u9078\uff0c\u5b89\u5168\u4e0d\u88ab\u5740",
                "size": "sm", "color": "#2E7D32", "weight": "bold", "wrap": True,
            })
        elif taxi_app:
            tip_contents.insert(0, {
                "type": "text",
                "text": f"\U0001f695 \u53eb\u8eca App\uff1a{taxi_app}",
                "size": "sm", "color": "#1565C0", "weight": "bold",
            })

        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#1565C0", "paddingAll": "14px",
                "contents": [
                    {"type": "text", "text": f"\u2728 {city} \u4ea4\u901a\u5c0f\u6492\u7a43",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                ],
            },
            "body": {"type": "box", "layout": "vertical",
                     "paddingAll": "12px",
                     "contents": tip_contents},
        })

    return [
        {"type": "text",
         "text": f"\U0001f687 {city}\u4ea4\u901a\u653b\u7565\n\u2190 \u5de6\u53f3\u6ed1\u52d5\u67e5\u770b"},
        {
            "type": "flex",
            "altText": f"\U0001f687 {city} \u4ea4\u901a\u653b\u7565",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]
