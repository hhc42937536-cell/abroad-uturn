"""簽證速查 — 台灣護照持有者適用"""

import json
import os

from bot.utils.date_parser import parse_destination
from bot.constants.cities import IATA_TO_COUNTRY

_data_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data"
)
_cache = {}


def _load_visa() -> dict:
    if "visa" in _cache:
        return _cache["visa"]
    try:
        with open(os.path.join(_data_dir, "visa_info.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["visa"] = data
        return data
    except Exception as e:
        print(f"[visa] Load error: {e}")
        return {}


# 熱門目的地快速對照
_POPULAR = [
    ("JP", "\U0001f1ef\U0001f1f5", "\u65e5\u672c"),
    ("KR", "\U0001f1f0\U0001f1f7", "\u97d3\u570b"),
    ("TH", "\U0001f1f9\U0001f1ed", "\u6cf0\u570b"),
    ("SG", "\U0001f1f8\U0001f1ec", "\u65b0\u52a0\u5761"),
    ("VN", "\U0001f1fb\U0001f1f3", "\u8d8a\u5357"),
    ("MY", "\U0001f1f2\U0001f1fe", "\u99ac\u4f86\u897f\u4e9e"),
    ("HK", "\U0001f1ed\U0001f1f0", "\u9999\u6e2f"),
    ("ID", "\U0001f1ee\U0001f1e9", "\u5370\u5c3c"),
    ("US", "\U0001f1fa\U0001f1f8", "\u7f8e\u570b"),
    ("GB", "\U0001f1ec\U0001f1e7", "\u82f1\u570b"),
    ("AU", "\U0001f1e6\U0001f1fa", "\u6fb3\u6d32"),
    ("FR", "\U0001f1eb\U0001f1f7", "\u6cd5\u570b"),
]

# 國家名 → 國家碼
_NAME_MAP = {
    "\u65e5\u672c": "JP", "\u6771\u4eac": "JP", "\u5927\u962a": "JP",
    "\u6c96\u7e04": "JP", "\u798f\u5ca1": "JP", "\u672d\u5e4c": "JP",
    "\u97d3\u570b": "KR", "\u9996\u723e": "KR", "\u91d8\u5c71": "KR",
    "\u6cf0\u570b": "TH", "\u66fc\u8c37": "TH", "\u6e05\u9083": "TH",
    "\u65b0\u52a0\u5761": "SG",
    "\u8d8a\u5357": "VN", "\u80e1\u5fd7\u660e": "VN", "\u6cb3\u5167": "VN",
    "\u99ac\u4f86\u897f\u4e9e": "MY", "\u5409\u9686\u5761": "MY",
    "\u9999\u6e2f": "HK",
    "\u6fb3\u9580": "MO",
    "\u5370\u5c3c": "ID", "\u5df4\u91cc\u5cf6": "ID",
    "\u83f2\u5f8b\u8cd3": "PH", "\u99bf\u5c3c\u62c9": "PH",
    "\u67ec\u57d4\u5be8": "KH", "\u5438\u5f15\u5e02": "KH",
    "\u7f05\u7538": "MM",
    "\u7f8e\u570b": "US",
    "\u82f1\u570b": "GB", "\u502b\u6566": "GB",
    "\u6cd5\u570b": "FR", "\u5df4\u9ece": "FR",
    "\u7fa9\u5927\u5229": "IT", "\u7f85\u99ac": "IT",
    "\u897f\u73ed\u7259": "ES", "\u5df4\u585e\u9686\u90a3": "ES",
    "\u5fb7\u570b": "DE", "\u67cf\u6797": "DE",
    "\u8377\u862d": "NL", "\u963f\u59c6\u65af\u7279\u4e39": "NL",
    "\u5967\u5730\u5229": "AT", "\u7dad\u4e5f\u7d0d": "AT",
    "\u6377\u514b": "CZ", "\u5e03\u62c9\u683c": "CZ",
    "\u745e\u58eb": "CH", "\u89e3\u6790": "CH",
    "\u571f\u8033\u5176": "TR", "\u4f0a\u65af\u5766\u5e03": "TR",
    "\u6fb3\u6d32": "AU", "\u6089\u5c3c": "AU",
    "\u7d10\u897f\u862d": "NZ", "\u5948\u827e\u767e": "NZ",
    "\u963f\u806f\u914b": "AE", "\u675c\u62dc": "AE",
    "\u5e1b\u7409": "PW",
    "\u95dc\u5cf6": "GU",
    "\u52a0\u62ff\u5927": "CA", "\u6eab\u54e5\u534e": "CA",
    "\u4e2d\u570b": "CN", "\u5317\u4eac": "CN", "\u4e0a\u6d77": "CN",
}


def handle_visa(text: str, user_id: str = "") -> list:
    """簽證速查入口"""
    clean = (text
             .replace("\u7c3d\u8b49", "")
             .replace("\u7c3d\u8b49\u67e5\u8a62", "")
             .replace("\u901f\u67e5", "")
             .replace("\u9700\u8981\u7c3d\u8b49\u55ce", "")
             .strip())

    if not clean:
        return _show_visa_overview()

    # 先試國家名對照
    for name, code in _NAME_MAP.items():
        if name in clean:
            return _show_visa_detail(code)

    # 再試 IATA 解析
    dest_code = parse_destination(clean)
    if dest_code:
        country = IATA_TO_COUNTRY.get(dest_code, "")
        if country:
            return _show_visa_detail(country)

    return [{"type": "text",
             "text": f"\u627e\u4e0d\u5230\u300c{clean}\u300d\u7684\u7c3d\u8b49\u8cc7\u8a0a\n\n"
                     f"\u53ef\u4ee5\u8a66\u8a66\uff1a\n"
                     f"\u2022 \u76f4\u63a5\u8f38\u5165\u570b\u5bb6\u540d\uff0c\u4f8b\u5982\u300c\u65e5\u672c\u300d\u300c\u6cf0\u570b\u300d\n"
                     f"\u2022 \u6216\u9ede\u4e0b\u65b9\u71b1\u9580\u76ee\u7684\u5730\u5feb\u901f\u67e5\u8a62"}]


def _show_visa_overview() -> list:
    """入口：熱門國家簽證總覽"""
    data = _load_visa()

    bubbles = []

    # Bubble 1: 免簽總覽卡
    free_lines = []
    visa_lines = []
    for code, flag, name in _POPULAR:
        info = data.get(code, {})
        vr = info.get("visa_required", False)
        limit = info.get("stay_limit", "")
        if vr is False:
            free_lines.append(
                {"type": "box", "layout": "horizontal", "margin": "sm",
                 "contents": [
                     {"type": "text", "text": f"{flag} {name}",
                      "size": "sm", "flex": 4, "color": "#333333"},
                     {"type": "text", "text": f"\u2705 \u514d\u7c3d {limit}",
                      "size": "sm", "flex": 6, "color": "#2E7D32", "align": "end"},
                 ]}
            )
        else:
            visa_lines.append(
                {"type": "box", "layout": "horizontal", "margin": "sm",
                 "contents": [
                     {"type": "text", "text": f"{flag} {name}",
                      "size": "sm", "flex": 4, "color": "#333333"},
                     {"type": "text", "text": f"\U0001f4cb {vr}",
                      "size": "sm", "flex": 6, "color": "#C62828", "align": "end"},
                 ]}
            )

    bubbles.append({
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1565C0", "paddingAll": "14px",
            "contents": [
                {"type": "text", "text": "\U0001f6c2 \u7c3d\u8b49\u901f\u67e5",
                 "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                {"type": "text", "text": "\u53f0\u7063\u8b77\u7167\u5132\u5b58\u7684\u6cd5\u5b9d",
                 "color": "#BBDEFB", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "xs",
            "contents": (
                [{"type": "text", "text": "\U0001f7e2 \u514d\u7c3d\u76ee\u7684\u5730",
                  "size": "xs", "color": "#888888", "weight": "bold", "margin": "sm"}]
                + free_lines
                + [{"type": "separator", "margin": "md"},
                   {"type": "text", "text": "\U0001f7e1 \u9700\u8981\u7c3d\u8b49 / \u96fb\u5b50\u7c3d",
                    "size": "xs", "color": "#888888", "weight": "bold", "margin": "sm"}]
                + visa_lines
            ),
        },
    })

    # Bubble 2+: 各國詳細卡（前6個）
    for code, flag, name in _POPULAR[:6]:
        info = data.get(code, {})
        if not info:
            continue
        bubbles.append(_visa_bubble(code, info, flag))

    qr_items = [
        {"type": "action", "action": {"type": "message",
         "label": f"{flag} {name}", "text": f"\u7c3d\u8b49 {name}"}}
        for code, flag, name in _POPULAR[:10]
    ]

    return [
        {"type": "text",
         "text": "\U0001f6c2 \u7c3d\u8b49\u901f\u67e5\uff08\u53f0\u7063\u8b77\u7167\uff09\n\u2190 \u5de6\u53f3\u6ed1\u52d5\uff0c\u6216\u9ede\u4e0b\u65b9\u76f4\u63a5\u67e5"},
        {
            "type": "flex",
            "altText": "\U0001f6c2 \u5404\u570b\u7c3d\u8b49\u901f\u67e5",
            "contents": {"type": "carousel", "contents": bubbles},
            "quickReply": {"items": qr_items},
        },
    ]


def _show_visa_detail(country_code: str) -> list:
    """顯示單一國家詳細簽證資訊"""
    data = _load_visa()
    info = data.get(country_code)
    if not info:
        return [{"type": "text", "text": "\u76ee\u524d\u9084\u6c92\u6709\u9019\u500b\u570b\u5bb6\u7684\u8cc7\u6599"}]

    # 找 flag
    flag = next((f for c, f, _ in _POPULAR if c == country_code), "\U0001f30d")
    bubble = _visa_bubble(country_code, info, flag)

    return [
        {
            "type": "flex",
            "altText": f"\U0001f6c2 {info.get('country_name', '')} \u7c3d\u8b49\u8cc7\u8a0a",
            "contents": bubble,
        }
    ]


def _visa_bubble(country_code: str, info: dict, flag: str) -> dict:
    """單國簽證 Flex Bubble"""
    vr = info.get("visa_required", False)
    country_name = info.get("country_name", country_code)
    stay = info.get("stay_limit", "")
    passport = info.get("passport_validity", "")
    notes = info.get("notes", "")
    entry_card = info.get("entry_card", False)

    if vr is False:
        status_text = "\u2705 \u514d\u7c3d\u5165\u5883"
        status_color = "#2E7D32"
        header_color = "#2E7D32"
    elif vr == "\u843d\u5730\u7c3d":
        status_text = "\U0001f7e1 \u843d\u5730\u7c3d"
        status_color = "#E65100"
        header_color = "#E65100"
    else:
        status_text = f"\U0001f4cb {vr}"
        status_color = "#C62828"
        header_color = "#C62828"

    rows = [
        _info_row("\u2708\ufe0f \u7c3d\u8b49\u72c0\u614b", status_text, status_color),
        _info_row("\U0001f4c5 \u53ef\u505c\u7559", stay),
        _info_row("\U0001f6c2 \u8b77\u7167\u6709\u6548\u671f", passport),
    ]
    if notes:
        rows.append(_info_row("\U0001f4a1 \u6ce8\u610f\u4e8b\u9805", notes, wrap=True))
    if entry_card:
        rows.append(_info_row("\U0001f4dd \u5165\u5883\u5361", "\u9700\u586b\u5beb\u5165\u5883\u5361\uff08\u6a5f\u4e0a\u6216\u7dda\u4e0a\uff09"))

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_color, "paddingAll": "14px",
            "contents": [
                {"type": "text",
                 "text": f"{flag} {country_name}",
                 "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                {"type": "text", "text": status_text,
                 "color": "#FFFFFF99", "size": "sm", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "14px", "spacing": "sm",
            "contents": rows,
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px",
            "contents": [
                {"type": "text",
                 "text": "\u26a0\ufe0f \u4ec5\u4f9b\u53c3\u8003\uff0c\u8acb\u4ee5\u5404\u570b\u5b98\u65b9\u516c\u544a\u70ba\u6e96",
                 "size": "xxs", "color": "#999999", "wrap": True},
            ],
        },
    }


def _info_row(label: str, value: str, color: str = "#444444", wrap: bool = False) -> dict:
    return {
        "type": "box", "layout": "horizontal", "margin": "sm",
        "contents": [
            {"type": "text", "text": label,
             "size": "xs", "color": "#888888", "flex": 4},
            {"type": "text", "text": value,
             "size": "sm", "color": color, "flex": 6,
             "wrap": wrap, "align": "end"},
        ],
    }
