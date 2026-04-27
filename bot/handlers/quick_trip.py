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
from bot.services.travelpayouts import search_cheapest_any
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
                     "action": {"type": "postback", "label": "📅 2 天（週末）",
                                "data": "quick_days=2", "displayText": "2 天"}},
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "📅 3 天（連假）",
                                "data": "quick_days=3", "displayText": "3 天"}},
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "📅 4 天",
                                "data": "quick_days=4", "displayText": "4 天"}},
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "📅 5 天",
                                "data": "quick_days=5", "displayText": "5 天"}},
                    {"type": "button", "style": "primary", "color": "#E91E63", "height": "sm",
                     "action": {"type": "postback", "label": "📅 7 天（一週）",
                                "data": "quick_days=7", "displayText": "7 天"}},
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
        from bot.utils.url_builder import google_explore_url
        return [{
            "type": "flex",
            "altText": "\u5373\u6642\u7968\u50f9\u66ab\u6642\u7121\u6cd5\u53d6\u5f97\uff0c\u8acb\u524d\u5f80\u8a02\u7968\u5e73\u53f0\u641c\u5c0b",
            "contents": {
                "type": "bubble", "size": "kilo",
                "body": {
                    "type": "box", "layout": "vertical",
                    "paddingAll": "18px", "spacing": "md",
                    "contents": [
                        {"type": "text", "text": "\u2708\ufe0f \u5373\u6642\u7968\u50f9\u66ab\u6642\u7121\u6cd5\u53d6\u5f97",
                         "weight": "bold", "size": "md", "color": "#333333"},
                        {"type": "text",
                         "text": "API \u66ab\u6642\u7121\u56de\u61c9\uff0c\u8acb\u524d\u5f80 Google Explore \u641c\u5c0b\u9644\u8fd1\u65e5\u671f\u7684\u4fbf\u5b9c\u76ee\u7684\u5730 \U0001f447",
                         "size": "sm", "color": "#888888", "wrap": True, "margin": "sm"},
                    ],
                },
                "footer": {
                    "type": "box", "layout": "vertical", "paddingAll": "10px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#4285F4",
                         "action": {"type": "uri", "label": "\U0001f310 Google Explore \u5168\u7403\u63a2\u7d22",
                                    "uri": google_explore_url(origin)}},
                    ],
                },
            },
        }]

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


def _ask_custom(user_id: str, idx: int) -> list:
    """選完方案後問有沒有特別需求"""
    update_session(user_id, {"quick_pending_pick": idx})
    return [{
        "type": "text",
        "text": "✈️ 好的！出發前最後一問：\n\n有什麼特別需求嗎？（幫我把行程規劃得更符合你）",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "postback",
                    "label": "🍜 美食探索", "data": "quick_custom=美食探索，想吃在地小吃和特色料理",
                    "displayText": "美食探索"}},
                {"type": "action", "action": {"type": "postback",
                    "label": "🏛 文化體驗", "data": "quick_custom=喜歡文化歷史，想參觀博物館和寺廟",
                    "displayText": "文化體驗"}},
                {"type": "action", "action": {"type": "postback",
                    "label": "🛍 購物行程", "data": "quick_custom=愛購物，想逛百貨商圈和特色市集",
                    "displayText": "購物行程"}},
                {"type": "action", "action": {"type": "postback",
                    "label": "👨‍👩‍👧 親子出遊", "data": "quick_custom=親子旅遊，有小孩同行",
                    "displayText": "親子出遊"}},
                {"type": "action", "action": {"type": "postback",
                    "label": "📸 拍照打卡", "data": "quick_custom=愛拍照打卡，想去網紅景點和絕美打卡地",
                    "displayText": "拍照打卡"}},
                {"type": "action", "action": {"type": "postback",
                    "label": "⭐ 追星/活動", "data": "quick_custom=追星旅遊或參加演唱會、特展等活動",
                    "displayText": "追星/活動"}},
                {"type": "action", "action": {"type": "postback",
                    "label": "⏭ 直接產出", "data": "quick_custom=",
                    "displayText": "直接產出"}},
            ],
        },
    }]


def handle_quick_pick(user_id: str, idx: int, custom: str = "") -> list:
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
        "hotel_preference": "市中心",
        "custom_requests": custom if custom else "說走就走快速規劃",
    }, step=8)

    from bot.handlers.trip_flow import _prompt_travel_info, _prompt_summary
    from bot.utils.itinerary_builder import build_itinerary_flex
    from bot.utils.budget_estimator import build_budget_bubble

    depart_date = chosen["departure_at"][:10]
    return_date = chosen["return_at"][:10]
    actual_days = chosen.get("days", 3)

    # ── 1. 行程大綱（Day 1~N 卡片 + 必吃清單）──
    itinerary_msgs = build_itinerary_flex(dest, depart_date, return_date, city_name)

    # ── 2. 行前須知（只取 Flex Carousel）──
    travel_msgs = _prompt_travel_info(user_id)
    flex_travel = [m for m in travel_msgs if m.get("type") == "flex"]

    # ── 3. 計畫摘要（機票/住宿/簽證/天氣/匯率，會清除 session）──
    summary_msgs = _prompt_summary(user_id)

    # ── 4. 預估支出 ──
    budget_bubble = build_budget_bubble(
        dest, city_name, actual_days, 1,
        chosen["price"],
        CITY_FLAG.get(dest, "✈️"),
    )
    budget_msg = {
        "type": "flex",
        "altText": f"💰 {city_name} 預估旅遊支出",
        "contents": budget_bubble,
    }

    # LINE 最多 5 則
    all_msgs = itinerary_msgs + flex_travel + summary_msgs + [budget_msg]
    return all_msgs[:5]
