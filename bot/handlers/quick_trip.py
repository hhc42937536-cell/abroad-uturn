"""🚀 說走就走模式（MVP）

極簡流程：
  使用者打「說走就走」
  → Bot 問「你有幾天假？」
  → Bot 自動找 3 個最便宜的目的地 + 合適日期
  → 每張卡片一鍵產出完整計畫書

重用既有模組：explore（找便宜）+ trip_flow.summary（產計畫）
"""

import datetime
import json

from bot.config import TRAVELPAYOUTS_TOKEN
from bot.constants.cities import IATA_TO_NAME, CITY_FLAG, IATA_TO_COUNTRY, TW_AIRPORTS, TW_ALL_AIRPORTS
from bot.constants.airlines import airline_name
from bot.services.travelpayouts import search_cheapest_any, mock_explore_data
from bot.session.manager import set_session, get_session, update_session
from bot.handlers.settings import get_user_origin


def handle_quick_trip(user_id: str, text: str = "") -> list:
    """說走就走主入口"""
    text = text.strip()

    # 初次進入
    if text in ("\u8aaa\u8d70\u5c31\u8d70", "\u8aaa\u8d70\u5c31\u98db", "\u99ac\u4e0a\u98db"):
        return _ask_days(user_id)

    # 使用者回覆天數
    if text.startswith("quick_days="):
        days = int(text.split("=")[1])
        return _find_options(user_id, days)

    # 預設回覆天數選擇
    return _ask_days(user_id)


def _ask_days(user_id: str) -> list:
    """問使用者有幾天假"""
    # 預先清除任何進行中的 session，避免衝突
    return [{
        "type": "flex",
        "altText": "\U0001f680 \u8aaa\u8d70\u5c31\u8d70",
        "contents": {
            "type": "bubble", "size": "mega",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E63", "paddingAll": "18px",
                "contents": [
                    {"type": "text", "text": "\U0001f680 \u8aaa\u8d70\u5c31\u8d70",
                     "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "\u61f6\u5f97\u898f\u5283\uff1f\u6211\u5e6b\u4f60\u76f4\u63a5\u7522\u51fa 3 \u500b\u300c\u4e00\u9375\u5168\u5305\u300d\u65b9\u6848",
                     "color": "#FFE0EC", "size": "sm", "margin": "sm", "wrap": True},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "md", "paddingAll": "18px",
                "contents": [
                    {"type": "text", "text": "\U0001f5d3\ufe0f \u4f60\u6709\u5e7e\u5929\u5047\uff1f",
                     "weight": "bold", "size": "md"},
                    {"type": "text", "text": "\u6211\u6703\u627e\u300c\u6700\u8fd1\u5c31\u80fd\u98db\u300d\u7684\u4fbf\u5b9c\u76ee\u7684\u5730",
                     "size": "sm", "color": "#888888"},
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "\U0001f4c6 2 \u5929\uff08\u9031\u672b\uff09",
                                "data": "quick_days=2", "displayText": "2 \u5929"}},
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "\U0001f4c6 3 \u5929\uff08\u9023\u5047\uff09",
                                "data": "quick_days=3", "displayText": "3 \u5929"}},
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "\U0001f4c6 4-5 \u5929",
                                "data": "quick_days=5", "displayText": "5 \u5929"}},
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "\U0001f4c6 \u4e00\u9031\u4ee5\u4e0a",
                                "data": "quick_days=7", "displayText": "7 \u5929"}},
                ],
            },
        },
    }]


def _find_options(user_id: str, days: int) -> list:
    """根據天數找 3 個便宜選項（「再找3個」會跳過已顯示過的目的地）"""
    origin = get_user_origin(user_id)

    # 讀取本輪已顯示過的目的地
    session = get_session(user_id) or {}
    shown_dests = set(session.get("quick_trip_shown", []))

    today = datetime.date.today()
    days_to_friday = (4 - today.weekday()) % 7
    if days_to_friday < 3:
        days_to_friday += 7
    depart_date = today + datetime.timedelta(days=days_to_friday)
    return_date = depart_date + datetime.timedelta(days=days - 1)

    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_cheapest_any(origin, limit=80)
    if not flights:
        flights = mock_explore_data(depart_date.strftime("%Y-%m"), origin)
    if not flights:
        return [{"type": "text", "text": "暫時找不到便宜方案，請稍後再試 🙏"}]

    def _build_seen(skip: set) -> dict:
        s = {}
        for f in flights:
            dest = f.get("destination", "")
            if not dest or dest in TW_ALL_AIRPORTS or dest in skip:
                continue
            if dest not in s or f.get("price", 99999) < s[dest].get("price", 99999):
                s[dest] = f
        return s

    # 按目的地去重（跳過已顯示）
    seen = _build_seen(shown_dests)

    # 如果跳過後沒剩，清空 shown_dests 重來
    if not seen:
        shown_dests = set()
        seen = _build_seen(shown_dests)

    # 過濾合理天數（±2 天），未來日期
    candidates = []
    for dest, f in seen.items():
        dep = f.get("departure_at", "")
        ret = f.get("return_at", "")
        if dep and ret and len(dep) >= 10 and len(ret) >= 10:
            try:
                d1 = datetime.date.fromisoformat(dep[:10])
                d2 = datetime.date.fromisoformat(ret[:10])
                actual_days = (d2 - d1).days + 1
                if abs(actual_days - days) <= 2 and d1 >= today:
                    f["_days"] = actual_days
                    candidates.append(f)
            except ValueError:
                continue

    if not candidates:
        candidates = sorted(seen.values(), key=lambda x: x.get("price", 99999))[:8]
        for c in candidates:
            c["_days"] = days

    candidates.sort(key=lambda x: x.get("price", 99999))
    top3 = candidates[:3]

    # 更新已顯示目的地
    new_shown = list(shown_dests | {f.get("destination", "") for f in top3})
    update_session(user_id, {"quick_trip_shown": new_shown})

    # 儲存到 session（使用者點選後用）
    quick_options = []
    for f in top3:
        quick_options.append({
            "destination": f.get("destination", ""),
            "price": f.get("price", 0),
            "airline": f.get("airline", ""),
            "departure_at": f.get("departure_at", depart_date.isoformat()),
            "return_at": f.get("return_at", return_date.isoformat()),
            "transfers": f.get("transfers", 0),
            "days": f.get("_days", days),
        })

    update_session(user_id, {
        "quick_trip_options": quick_options,
        "quick_trip_origin": origin,
    })

    # 建立 3 張「一鍵全包」卡片
    bubbles = []
    for i, opt in enumerate(top3):
        bubbles.append(_build_option_card(i, opt, days))

    # 最後一張：重找
    bubbles.append({
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical",
            "justifyContent": "center", "alignItems": "center",
            "paddingAll": "20px", "spacing": "md",
            "contents": [
                {"type": "text", "text": "\U0001f504", "size": "3xl", "align": "center"},
                {"type": "text", "text": "\u6c92\u559c\u6b61\u7684\uff1f",
                 "weight": "bold", "size": "md", "align": "center"},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px", "spacing": "sm",
            "contents": [
                {"type": "button", "style": "secondary", "height": "sm",
                 "action": {"type": "postback", "label": "\u518d\u627e 3 \u500b",
                            "data": f"quick_days={days}", "displayText": "\u518d\u627e"}},
                {"type": "button", "style": "secondary", "height": "sm",
                 "action": {"type": "message", "label": "\u6211\u8981\u8a73\u7d30\u898f\u5283",
                            "text": "\u958b\u59cb\u898f\u5283"}},
            ],
        },
    })

    return [
        {"type": "text", "text":
            f"\U0001f680 \u5e6b\u4f60\u627e\u5230 3 \u500b\u300c\u8aaa\u8d70\u5c31\u8d70\u300d\u65b9\u6848\uff08{days} \u5929\uff09\n"
            f"\u2190 \u5de6\u53f3\u6ed1\u52d5 \u2022 \u9ede\u300c\u5c31\u9019\u500b\uff01\u300d\u4e00\u9375\u7522\u51fa\u5b8c\u6574\u8a08\u756b"},
        {
            "type": "flex",
            "altText": "\u8aaa\u8d70\u5c31\u8d70 \u2013 3 \u500b\u65b9\u6848",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def _build_option_card(idx: int, opt: dict, requested_days: int) -> dict:
    """單張方案卡片"""
    dest = opt["destination"]
    city_name = IATA_TO_NAME.get(dest, dest)
    flag = CITY_FLAG.get(dest, "\u2708\ufe0f")
    price = opt["price"]
    airline = airline_name(opt["airline"])
    transfers = opt.get("transfers", 0)
    actual_days = opt.get("days", requested_days)
    transfer_text = "\u76f4\u98db" if transfers == 0 else f"\u8f49\u6a5f{transfers}\u6b21"

    dep = opt["departure_at"][:10]
    ret = opt["return_at"][:10]
    try:
        d1 = datetime.date.fromisoformat(dep)
        d2 = datetime.date.fromisoformat(ret)
        date_text = f"{d1.month}/{d1.day} \u2192 {d2.month}/{d2.day}"
    except Exception:
        date_text = f"{dep} ~ {ret}"

    header_colors = ["#E91E63", "#9C27B0", "#FF6B35"]
    rank_labels = ["\U0001f947 \u6700\u4fbf\u5b9c", "\U0001f948 \u7b2c\u4e8c\u4f4e", "\U0001f949 \u7b2c\u4e09\u4f4e"]

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_colors[idx % 3], "paddingAll": "15px",
            "contents": [
                {"type": "text", "text": rank_labels[idx] if idx < 3 else "",
                 "color": "#FFFFFF", "size": "xs", "weight": "bold"},
                {"type": "text", "text": f"{flag} {city_name}",
                 "color": "#FFFFFF", "weight": "bold", "size": "xl", "margin": "sm"},
                {"type": "text", "text": f"{actual_days} \u5929{max(actual_days - 1, 0)} \u591c",
                 "color": "#FFFFFFCC", "size": "sm"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "15px",
            "contents": [
                {"type": "text", "text": f"NT$ {price:,}",
                 "size": "xxl", "weight": "bold", "color": "#E53935"},
                {"type": "text", "text": "\u6a5f\u7968\u542b\u7a05\u7e3d\u50f9",
                 "size": "xxs", "color": "#999999"},
                {"type": "separator", "margin": "md"},
                {"type": "text", "text": f"\U0001f4c5 {date_text}",
                 "size": "sm", "color": "#555555", "margin": "md"},
                {"type": "text", "text": f"\u2708\ufe0f {airline} \u2022 {transfer_text}",
                 "size": "sm", "color": "#555555"},
                {"type": "text", "text": "\u2728 \u6a5f\u7968 + \u98ef\u5e97 + \u884c\u524d\u9808\u77e5\n\u5168\u5305\uff0c1 \u500b\u6309\u9215\u642e\u5b9a",
                 "size": "xs", "color": "#4CAF50", "margin": "md", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "10px",
            "contents": [
                {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                 "action": {"type": "postback",
                            "label": "\U0001f525 \u5c31\u9019\u500b\uff01\u4e00\u9375\u5168\u5305",
                            "data": f"quick_pick={idx}",
                            "displayText": f"\u5c31\u9078 {city_name}\uff01"}},
            ],
        },
    }


def handle_quick_pick(user_id: str, idx: int) -> list:
    """使用者選了某個方案 → 產出完整計畫書"""
    session = get_session(user_id) or {}
    options = session.get("quick_trip_options", [])
    origin = session.get("quick_trip_origin", "TPE")

    if idx >= len(options):
        return [{"type": "text", "text": "\u65b9\u6848\u5df2\u904e\u671f\uff0c\u8acb\u91cd\u65b0\u8f38\u5165\u300c\u8aaa\u8d70\u5c31\u8d70\u300d"}]

    chosen = options[idx]
    dest = chosen["destination"]
    city_name = IATA_TO_NAME.get(dest, dest)
    country = IATA_TO_COUNTRY.get(dest, "")

    # 填充 session 資料（讓 summary 可以產出完整計畫書）
    update_session(user_id, {
        "destination_code": dest,
        "destination_name": city_name,
        "country_code": country,
        "depart_date": chosen["departure_at"][:10],
        "return_date": chosen["return_at"][:10],
        "flexibility": "specific",
        "adults": 1,
        "children": 0,
        "budget": chosen["price"] * 2,  # 預設預算 = 機票 × 2（給飯店雜支）
        "origin": origin,
        "flight_choice": chosen,
        "flight_choice_display": f"NT${chosen['price']:,} ({airline_name(chosen['airline'])})",
        "hotel_preference": "\u5e02\u4e2d\u5fc3",
        "custom_requests": "\u8aaa\u8d70\u5c31\u8d70\u5feb\u901f\u898f\u5283",
    }, step=8)

    from bot.handlers.trip_flow import _prompt_travel_info, _prompt_summary
    from bot.utils.itinerary_builder import build_itinerary_flex

    depart_date = chosen["departure_at"][:10]
    return_date = chosen["return_at"][:10]

    # ── 1. 行程大綱（Day 1~N 卡片 + 必吃清單）──
    itinerary_msgs = build_itinerary_flex(dest, depart_date, return_date, city_name)

    # ── 2. 行前須知（只取 Flex Carousel，不要前後文字框，省則數）──
    travel_msgs = _prompt_travel_info(user_id)
    flex_travel = [m for m in travel_msgs if m.get("type") == "flex"]

    # ── 3. 計畫摘要（機票/住宿/簽證/天氣/匯率，會清除 session）──
    summary_msgs = _prompt_summary(user_id)

    # LINE 最多 5 則：行程文字(1) + 行程Flex(1) + 行前須知Flex(1) + 計畫書(1) = 4 則
    return (itinerary_msgs + flex_travel + summary_msgs)[:5]
