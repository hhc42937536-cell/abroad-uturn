"""8 步引導式旅程規劃流程控制器（狀態機核心）

Phase 2 會完整實作每個步驟。目前先建立骨架。
"""

from bot.session.manager import (
    get_session, get_step, set_session, update_session,
    clear_session, start_session,
)
from bot.handlers.settings import get_user_origin
from bot.flex.progress_bar import progress_text


def start(user_id: str) -> list:
    """步驟 0：進入規劃模式"""
    origin = get_user_origin(user_id)
    start_session(user_id, origin)

    return [
        {
            "type": "flex",
            "altText": "\u2728 \u958b\u59cb\u898f\u5283\u65c5\u7a0b",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "20px",
                    "contents": [
                        {"type": "text", "text": "\u2728 \u51fa\u570b\u512a\u8f49 - \u5b8c\u6574\u65c5\u7a0b\u898f\u5283",
                         "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "\u6211\u6703\u50cf\u4f60\u7684\u5c08\u5c6c\u65c5\u884c\u9867\u554f\uff0c\u5e36\u4f60\u5f9e\u982d\u5230\u5c3e\u898f\u5283\u4e00\u6b21\u65c5\u884c\u3002",
                         "color": "#FFE0CC", "size": "sm", "margin": "md", "wrap": True},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "md", "paddingAll": "20px",
                    "contents": [
                        {"type": "text", "text": "\U0001f4cb \u898f\u5283\u6d41\u7a0b", "weight": "bold", "size": "md"},
                        {"type": "separator"},
                        {"type": "text", "text":
                            "\u2460 \u9078\u76ee\u7684\u5730\n"
                            "\u2461 \u9078\u65e5\u671f\n"
                            "\u2462 \u4eba\u6578\u8207\u9810\u7b97\n"
                            "\u2463 \u6a5f\u7968\u63a8\u85a6\n"
                            "\u2464 \u4f4f\u5bbf\u63a8\u85a6\n"
                            "\u2465 \u884c\u7a0b\u5927\u7db1\n"
                            "\u2466 \u884c\u524d\u9808\u77e5\n"
                            "\u2467 \u5b8c\u6574\u8a08\u756b\u66f8",
                         "size": "sm", "color": "#555555", "wrap": True},
                        {"type": "text", "text": "\u6574\u500b\u904e\u7a0b\u5927\u7d04 5-8 \u5206\u9418\u5373\u53ef\u5b8c\u6210\u3002",
                         "size": "xs", "color": "#999999", "margin": "md"},
                    ],
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#FF6B35",
                         "action": {"type": "postback", "label": "\U0001f680 \u958b\u59cb\u898f\u5283\uff01",
                                    "data": "trip_step=1", "displayText": "\u958b\u59cb\u898f\u5283\uff01"}},
                    ],
                },
            },
        }
    ]


def start_with_destination(user_id: str, text: str) -> list:
    """從智慧偵測直接啟動規劃，跳過歡迎頁，直接到步驟 1（確認目的地）"""
    origin = get_user_origin(user_id)
    start_session(user_id, origin)
    return _step1_destination(user_id, text)


def handle_step(user_id: str, text: str, step: int) -> list:
    """根據目前步驟處理使用者輸入"""
    handlers = {
        1: _step1_destination,
        2: _step2_dates,
        3: _step3_travelers,
        4: _step4_flights,
        5: _step5_hotels,
        6: _step6_itinerary,
        7: _step7_travel_info,
        8: _step8_summary,
    }

    handler = handlers.get(step)
    if handler:
        return handler(user_id, text)

    # 預設：顯示目前步驟提示
    return [{"type": "text", "text": f"{progress_text(step)}\n\n\u8acb\u7e7c\u7e8c\u8f38\u5165\u8cc7\u6599\uff0c\u6216\u8f38\u5165\u300c\u53d6\u6d88\u898f\u5283\u300d\u4e2d\u6b62\u3002"}]


def handle_postback(user_id: str, data: str) -> list:
    """處理 postback 事件（步驟導航按鈕）"""
    import urllib.parse
    params = dict(urllib.parse.parse_qsl(data))

    if "trip_step" in params:
        target_step = int(params["trip_step"])
        session = get_session(user_id)
        if not session:
            return start(user_id)

        from bot.session.manager import set_session
        set_session(user_id, session, step=target_step)
        # 進入步驟 8（計畫書）時，先插入行程大綱再顯示計畫書
        if target_step == 8:
            from bot.utils.itinerary_builder import build_itinerary_flex
            dest = session.get("destination_code", "")
            city = session.get("destination_name", "")
            depart = session.get("depart_date", "")
            ret = session.get("return_date", "")
            itinerary_msgs = build_itinerary_flex(dest, depart, ret, city) if dest and depart else []
            summary_msgs = _prompt_summary(user_id)
            return (itinerary_msgs + summary_msgs)[:5]
        return _show_step_prompt(user_id, target_step)

    if "trip_select" in params:
        # 處理步驟內的選擇（例如選機票）
        return _handle_selection(user_id, params)

    # ── 說走就走的 postback ──
    if "quick_days" in params:
        from bot.handlers.quick_trip import _find_options
        return _find_options(user_id, int(params["quick_days"]))

    if "quick_pick" in params:
        from bot.handlers.quick_trip import handle_quick_pick
        return handle_quick_pick(user_id, int(params["quick_pick"]))

    return []


def _show_step_prompt(user_id: str, step: int) -> list:
    """顯示指定步驟的提示訊息"""
    prompts = {
        1: _prompt_destination,
        2: _prompt_dates,
        3: _prompt_travelers,
        4: _prompt_flights,
        5: _prompt_hotels,
        6: _prompt_itinerary,
        7: _prompt_travel_info,
        8: _prompt_summary,
    }
    fn = prompts.get(step)
    if fn:
        return fn(user_id)
    return [{"type": "text", "text": "\u898f\u5283\u5df2\u5b8c\u6210\uff01"}]


# ─── 步驟 1：目的地 ──────────────────────────────────

def _prompt_destination(user_id: str) -> list:
    return [{
        "type": "text", "text":
            f"[1/8] \u76ee\u7684\u5730\n\n"
            f"\u597d\u7684\uff01\u7b2c\u4e00\u6b65\uff1a\n\n"
            f"\u4f60\u9019\u6b21\u6700\u60f3\u53bb\u54ea\u500b\u570b\u5bb6\u6216\u57ce\u5e02\u5462\uff1f\n\n"
            f"\u53ef\u4ee5\u76f4\u63a5\u8f38\u5165\uff0c\u4f8b\u5982\uff1a\n"
            f"\u2022 \u65e5\u672c\u6771\u4eac\n"
            f"\u2022 \u6cf0\u570b\u66fc\u8c37\n"
            f"\u2022 \u97d3\u570b\u9996\u723e\n"
            f"\u2022 \u7fa9\u5927\u5229\u7f85\u99ac",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "\U0001f1ef\U0001f1f5 \u65e5\u672c", "text": "\u6771\u4eac"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f1f0\U0001f1f7 \u97d3\u570b", "text": "\u9996\u723e"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f1f9\U0001f1ed \u6cf0\u570b", "text": "\u66fc\u8c37"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f30d \u5e6b\u6211\u63a8\u85a6", "text": "\u63a8\u85a6\u76ee\u7684\u5730"}},
            ],
        },
    }]


def _step1_destination(user_id: str, text: str) -> list:
    from bot.utils.date_parser import parse_destination
    from bot.constants.cities import IATA_TO_NAME, IATA_TO_COUNTRY

    if text in ("\u63a8\u85a6\u76ee\u7684\u5730", "\u5e6b\u6211\u63a8\u85a6"):
        from bot.handlers.explore import handle_quick_explore
        session = get_session(user_id)
        origin = session.get("origin", "TPE") if session else "TPE"
        return handle_quick_explore(origin) + [
            {"type": "text", "text": "\u770b\u5230\u559c\u6b61\u7684\u76ee\u7684\u5730\u4e86\u55ce\uff1f\u8acb\u76f4\u63a5\u8f38\u5165\u57ce\u5e02\u540d\u5373\u53ef\u7e7c\u7e8c\u898f\u5283\uff01"}
        ]

    dest_code = parse_destination(text)
    if not dest_code:
        return [{"type": "text", "text":
            "\u6211\u627e\u4e0d\u5230\u9019\u500b\u76ee\u7684\u5730\uff0c\u8acb\u8a66\u8a66\u8f38\u5165\u57ce\u5e02\u540d\u7a31\uff0c\u4f8b\u5982\uff1a\n"
            "\u300c\u6771\u4eac\u300d\u300c\u66fc\u8c37\u300d\u300c\u9996\u723e\u300d"
        }]

    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    country_code = IATA_TO_COUNTRY.get(dest_code, "")

    update_session(user_id, {
        "destination_code": dest_code,
        "destination_name": city_name,
        "country_code": country_code,
    }, step=2)

    return [{
        "type": "text", "text":
            f"[2/8] \u65e5\u671f\n\n"
            f"\u76ee\u7684\u5730\uff1a{city_name} \u2705\n\n"
            f"\u7b2c\u4e8c\u6b65\uff1a\u4f60\u9810\u8a08\u4ec0\u9ebc\u6642\u5019\u51fa\u767c\uff1f\n\n"
            f"\u8acb\u9078\u64c7\u6216\u8f38\u5165\uff1a\n"
            f"\u2022 \u76f4\u63a5\u8f38\u5165\u65e5\u671f\uff0c\u4f8b\u5982\u300c6/15-6/22\u300d\n"
            f"\u2022 \u6216\u8f38\u5165\u6708\u4efd\uff0c\u4f8b\u5982\u300c6\u6708\u300d",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "\u4e0b\u9031", "text": "\u4e0b\u9031"}},
                {"type": "action", "action": {"type": "message", "label": "\u4e0b\u500b\u6708", "text": "\u4e0b\u500b\u6708"}},
                {"type": "action", "action": {"type": "message", "label": "\u6700\u8fd1\u6709\u5047\u5c31\u8d70", "text": "\u5f48\u6027"}},
                {"type": "action", "action": {"type": "message", "label": "\u6691\u5047", "text": "7\u6708"}},
                {"type": "action", "action": {"type": "message", "label": "\u5e74\u5e95", "text": "12\u6708"}},
            ],
        },
    }]


# ─── 步驟 2：日期 ────────────────────────────────────

def _prompt_dates(user_id: str) -> list:
    session = get_session(user_id) or {}
    city = session.get("destination_name", "")
    return [{"type": "text", "text":
        f"[2/8] \u65e5\u671f\n\n"
        f"\u76ee\u7684\u5730\uff1a{city}\n\n"
        f"\u4f60\u9810\u8a08\u4ec0\u9ebc\u6642\u5019\u51fa\u767c\uff1f\n"
        f"\u4f8b\u5982\uff1a\u300c6/15-6/22\u300d\u6216\u300c6\u6708\u300d",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "\u5f48\u6027\u65e5\u671f", "text": "\u5f48\u6027"}},
                {"type": "action", "action": {"type": "message", "label": "\u4e0b\u500b\u6708", "text": "\u4e0b\u500b\u6708"}},
            ],
        },
    }]


def _step2_dates(user_id: str, text: str) -> list:
    from bot.utils.date_parser import parse_date_range, parse_month
    import datetime

    session = get_session(user_id) or {}

    if text in ("\u5f48\u6027", "\u6700\u8fd1\u6709\u5047\u5c31\u8d70"):
        today = datetime.date.today()
        next_month = f"{today.year}-{today.month + 1:02d}" if today.month < 12 else f"{today.year + 1}-01"
        update_session(user_id, {
            "flexibility": "flexible",
            "depart_date": next_month,
            "return_date": "",
        }, step=3)
        return _prompt_travelers(user_id)

    if text == "\u4e0b\u500b\u6708":
        today = datetime.date.today()
        next_month = f"{today.year}-{today.month + 1:02d}" if today.month < 12 else f"{today.year + 1}-01"
        update_session(user_id, {
            "flexibility": "month",
            "depart_date": next_month,
            "return_date": "",
        }, step=3)
        return _prompt_travelers(user_id)

    # 嘗試解析月份
    month = parse_month(text)
    if month and not parse_date_range(text)[0]:
        update_session(user_id, {
            "flexibility": "month",
            "depart_date": month,
            "return_date": "",
        }, step=3)
        return _prompt_travelers(user_id)

    # 嘗試解析日期範圍
    depart, ret = parse_date_range(text)
    if depart:
        update_session(user_id, {
            "flexibility": "specific",
            "depart_date": depart,
            "return_date": ret,
        }, step=3)
        return _prompt_travelers(user_id)

    return [{"type": "text", "text":
        "\u6211\u770b\u4e0d\u61c2\u65e5\u671f\uff0c\u8acb\u8a66\u8a66\uff1a\n"
        "\u300c6/15-6/22\u300d\u300c7\u6708\u300d\u300c\u4e0b\u500b\u6708\u300d"
    }]


# ─── 步驟 3：人數與預算 ──────────────────────────────

def _prompt_travelers(user_id: str) -> list:
    session = get_session(user_id) or {}
    city = session.get("destination_name", "")
    dates = session.get("depart_date", "")
    flex = session.get("flexibility", "")

    date_display = dates
    if flex == "flexible":
        date_display = "\u5f48\u6027\u65e5\u671f"
    elif flex == "month" and dates:
        date_display = f"{dates[5:]}\u6708"

    return [{
        "type": "text", "text":
            f"[3/8] \u4eba\u6578\u8207\u9810\u7b97\n\n"
            f"\u76ee\u7684\u5730\uff1a{city}\n"
            f"\u65e5\u671f\uff1a{date_display}\n\n"
            f"\u7b2c\u4e09\u6b65\uff1a\u9019\u6b21\u7e3d\u5171\u6709\u5e7e\u500b\u4eba\u8981\u53bb\u5462\uff1f",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "1 人獨旅", "text": "1人"}},
                {"type": "action", "action": {"type": "message", "label": "2 人同行", "text": "2人"}},
                {"type": "action", "action": {"type": "message", "label": "3 人", "text": "3人"}},
                {"type": "action", "action": {"type": "message", "label": "4 人", "text": "4人"}},
                {"type": "action", "action": {"type": "message", "label": "5人以上", "text": "5人"}},
            ],
        },
    }]


def _step3_travelers(user_id: str, text: str) -> list:
    import re

    # 解析人數
    m = re.search(r"(\d+)", text)
    if not m:
        return [{"type": "text", "text": "\u8acb\u544a\u8a34\u6211\u4eba\u6578\uff0c\u4f8b\u5982\uff1a\u300c2\u4eba\u300d"}]

    adults = int(m.group(1))
    session = get_session(user_id) or {}

    # 如果還沒問預算，先存人數再問預算
    if not session.get("budget"):
        update_session(user_id, {"adults": adults, "children": 0})
        return [{
            "type": "text", "text":
                f"\u597d\u7684\uff0c{adults} \u4eba\u51fa\u767c\uff01\n\n"
                f"\u9019\u8ddf\u65c5\u884c\u7684\u7e3d\u9810\u7b97\u5927\u7d04\u662f\u591a\u5c11\uff1f\uff08\u53f0\u5e63\uff09",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "3萬以下", "text": "預算3萬"}},
                    {"type": "action", "action": {"type": "message", "label": "3~6萬", "text": "預算6萬"}},
                    {"type": "action", "action": {"type": "message", "label": "6~10萬", "text": "預算10萬"}},
                    {"type": "action", "action": {"type": "message", "label": "10~20萬", "text": "預算15萬"}},
                    {"type": "action", "action": {"type": "message", "label": "20萬以上", "text": "預算25萬"}},
                ],
            },
        }]

    return _prompt_budget_response(user_id, text)


def _prompt_budget_response(user_id: str, text: str) -> list:
    """解析預算並進入步驟 4（自動搜尋機票）"""
    import re

    budget_map = {
        # 舊格式（向下相容）
        "5萬以下": 50000, "預算5萬": 50000,
        "5-10萬": 100000, "預算10萬": 100000,
        "10-15萬": 150000, "預算15萬": 150000,
        "15萬以上": 200000, "預算20萬": 200000,
        # 新格式
        "預算3萬": 30000, "3萬以下": 30000,
        "預算6萬": 60000, "3~6萬": 60000,
        "6~10萬": 100000,
        "10~20萬": 150000,
        "預算25萬": 250000, "20萬以上": 250000,
    }

    budget = budget_map.get(text)
    if not budget:
        m = re.search(r"(\d+)", text)
        if m:
            num = int(m.group(1))
            budget = num * 10000 if num < 1000 else num
        else:
            budget = 100000

    update_session(user_id, {"budget": budget}, step=4)

    # 自動進入步驟 4：搜尋機票
    return _prompt_flights(user_id)


# ─── 步驟 4：機票推薦 ────────────────────────────────

def _prompt_flights(user_id: str) -> list:
    """根據 session 資料搜尋機票並顯示推薦"""
    from bot.config import TRAVELPAYOUTS_TOKEN
    from bot.constants.cities import IATA_TO_NAME, TW_AIRPORTS
    from bot.services.travelpayouts import search_flights, search_cheapest_by_month
    from bot.utils.url_builder import skyscanner_url, google_flights_url
    from bot.flex.flight_bubble import flight_bubble
    from bot.flex.progress_bar import build_progress_bar

    session = get_session(user_id) or {}
    origin = session.get("origin", "TPE")
    dest = session.get("destination_code", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    flex = session.get("flexibility", "specific")
    budget = session.get("budget", 0)
    adults = session.get("adults", 1)
    city_name = session.get("destination_name", dest)

    if not dest:
        return [{"type": "text", "text": "\u627e\u4e0d\u5230\u76ee\u7684\u5730\u8cc7\u8a0a\uff0c\u8acb\u8f38\u5165\u300c\u53d6\u6d88\u898f\u5283\u300d\u91cd\u65b0\u958b\u59cb"}]

    # 搜尋機票
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        if flex == "month":
            flights = search_cheapest_by_month(origin, depart)
            if flights:
                flights = [f for f in flights if f.get("destination") == dest]
        elif depart:
            flights = search_flights(origin, dest, depart, ret)

    if not flights:
        update_session(user_id, {}, step=5)
        sky = skyscanner_url(origin, dest, depart or "", ret or "")
        gf = google_flights_url(origin, dest, depart or "", ret or "")
        return [{"type": "text", "text":
            f"[4/8] \u6a5f\u7968\u63a8\u85a6\n\n"
            f"\u2708\ufe0f \u5373\u6642\u7968\u50f9\u66ab\u6642\u7121\u6cd5\u53d6\u5f97\uff0c\u8df3\u904e\u6a5f\u7968\u6b65\u9a5f\u3002\n"
            f"\U0001f50d Skyscanner\uff1a{sky}\n"
            f"\U0001f50d Google Flights\uff1a{gf}"
        }] + _prompt_hotels(user_id)

    # 排序：價格低到高
    flights.sort(key=lambda x: x.get("price", 99999))

    # 如果有預算限制，標記超出預算的
    per_person_budget = budget // adults if adults > 0 else budget

    # 取前 5 個
    top_flights = flights[:5]

    # 建立機票卡片（帶「選這個」postback 按鈕）
    bubbles = []
    for i, f in enumerate(top_flights):
        price = f.get("price", 0)
        bubble = flight_bubble(f, i, show_track_btn=False)

        # 替換 footer：加入「選這個」按鈕
        flight_id = f"{f.get('airline', '')}-{f.get('departure_at', '')}-{price}"
        select_btn = {
            "type": "button", "style": "primary", "color": "#FF6B35", "height": "sm",
            "action": {
                "type": "postback",
                "label": "\u2705 \u9078\u9019\u500b\u65b9\u6848",
                "data": f"trip_select=flight&idx={i}&price={price}&airline={f.get('airline', '')}",
                "displayText": f"\u6211\u9078\u64c7\u65b9\u6848 {i+1}",
            },
        }

        # 預算提示
        if per_person_budget > 0 and price > per_person_budget:
            bubble["body"]["contents"].append({
                "type": "text", "text": "\u26a0\ufe0f \u8d85\u51fa\u4eba\u5747\u9810\u7b97",
                "size": "xs", "color": "#E53935", "margin": "sm",
            })
        elif per_person_budget > 0 and price <= per_person_budget * 0.7:
            bubble["body"]["contents"].append({
                "type": "text", "text": "\U0001f4b0 \u6027\u50f9\u6bd4\u6975\u9ad8",
                "size": "xs", "color": "#4CAF50", "margin": "sm",
            })

        # 在 footer 最前面加入選擇按鈕
        bubble["footer"]["contents"].insert(0, select_btn)
        bubbles.append(bubble)

    # 加一張「跳過」卡片
    bubbles.append({
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical",
            "justifyContent": "center", "alignItems": "center",
            "paddingAll": "20px", "spacing": "md",
            "contents": [
                {"type": "text", "text": "\u23ed\ufe0f", "size": "3xl", "align": "center"},
                {"type": "text", "text": "\u5148\u8df3\u904e\u6a5f\u7968", "weight": "bold", "size": "md", "align": "center"},
                {"type": "text", "text": "\u7a0d\u5f8c\u518d\u6c7a\u5b9a\u6a5f\u7968",
                 "size": "sm", "color": "#888888", "align": "center", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px",
            "contents": [
                {"type": "button", "style": "secondary", "height": "sm",
                 "action": {"type": "postback", "label": "\u8df3\u904e\uff0c\u7e7c\u7e8c\u4f4f\u5bbf",
                            "data": "trip_step=5", "displayText": "\u8df3\u904e\u6a5f\u7968"}},
            ],
        },
    })

    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    date_display = _format_dates(session)

    # 儲存搜尋到的機票資料（供後續使用）
    update_session(user_id, {"flight_results": [
        {"price": f.get("price"), "airline": f.get("airline"), "transfers": f.get("transfers"),
         "departure_at": f.get("departure_at"), "return_at": f.get("return_at"),
         "origin": f.get("origin"), "destination": f.get("destination")}
        for f in top_flights
    ]})

    return [
        {"type": "text", "text":
            f"[4/8] \u6a5f\u7968\u63a8\u85a6\n\n"
            f"\u2708\ufe0f {origin_name} \u2192 {city_name}\n"
            f"\U0001f4c5 {date_display}\n"
            f"\U0001f465 {adults} \u4eba\n\n"
            f"\u6839\u64da\u4f60\u7684\u689d\u4ef6\uff0c\u627e\u5230\u4ee5\u4e0b\u6a5f\u7968\u65b9\u6848\uff1a\n"
            f"\uff08\u5de6\u53f3\u6ed1\u52d5\u67e5\u770b\u66f4\u591a\uff0c\u9ede\u300c\u9078\u9019\u500b\u65b9\u6848\u300d\u7e7c\u7e8c\uff09"
        },
        {
            "type": "flex",
            "altText": f"{city_name} \u6a5f\u7968\u63a8\u85a6",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def _step4_flights(user_id: str, text: str) -> list:
    """步驟 4：使用者可能在此步驟輸入文字（通常是透過 postback 選擇）"""
    # 如果使用者直接打字，跳到下一步
    update_session(user_id, {}, step=5)
    return _prompt_hotels(user_id)


# ─── 步驟 5：住宿推薦 ────────────────────────────────

def _prompt_hotels(user_id: str) -> list:
    """根據目的地和日期產生多平台飯店連結"""
    from bot.constants.cities import IATA_TO_NAME, AGODA_CITY_KEYWORDS
    from bot.utils.url_builder import agoda_url, booking_url
    from bot.flex.progress_bar import build_progress_bar
    from bot.handlers.hotels import _get_estimate

    session = get_session(user_id) or {}
    dest = session.get("destination_code", "")
    city_name = session.get("destination_name", dest)
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    city_kw = AGODA_CITY_KEYWORDS.get(dest, city_name)
    date_display = _format_dates(session)
    est = _get_estimate(dest)

    agoda = agoda_url(city_kw, depart, ret)
    booking = booking_url(city_kw)

    # Trip.com 連結
    trip_com = f"https://www.trip.com/hotels/?city={city_kw}&locale=zh-TW&curr=TWD"

    return [
        {
            "type": "flex",
            "altText": f"[5/8] {city_name} \u4f4f\u5bbf\u63a8\u85a6",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#E91E8C", "paddingAll": "15px",
                    "contents": [
                        build_progress_bar(5),
                        {"type": "text", "text": f"\U0001f3e8 {city_name} \u4f4f\u5bbf\u63a8\u85a6",
                         "color": "#FFFFFF", "weight": "bold", "size": "lg", "margin": "md"},
                        {"type": "text", "text": f"\U0001f4c5 {date_display}",
                         "color": "#FFE0CC", "size": "sm", "margin": "xs"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "md", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "\u4f60\u504f\u597d\u4f4f\u5728\u54ea\u500b\u5340\u57df\uff1f",
                         "weight": "bold", "size": "md"},
                        # 估算資訊卡
                        {
                            "type": "box", "layout": "horizontal",
                            "backgroundColor": "#FFF0F5", "paddingAll": "10px",
                            "cornerRadius": "8px", "margin": "sm",
                            "contents": [
                                {"type": "box", "layout": "vertical", "flex": 1, "contents": [
                                    {"type": "text", "text": "\U0001f4b0 \u4f30\u7b97\u5468\u5747",
                                     "size": "xxs", "color": "#C2185B", "weight": "bold"},
                                    {"type": "text", "text": f"NT$ {est['price']}/\u6674",
                                     "size": "xs", "color": "#333333", "weight": "bold"},
                                ]},
                                {"type": "box", "layout": "vertical", "flex": 1, "contents": [
                                    {"type": "text", "text": "\u2b50 \u8a55\u5206",
                                     "size": "xxs", "color": "#C2185B", "weight": "bold"},
                                    {"type": "text", "text": est["rating"],
                                     "size": "xs", "color": "#333333", "weight": "bold"},
                                ]},
                                {"type": "box", "layout": "vertical", "flex": 2, "contents": [
                                    {"type": "text", "text": "\U0001f4cd \u63a8\u85a6\u5340\u57df",
                                     "size": "xxs", "color": "#C2185B", "weight": "bold"},
                                    {"type": "text", "text": est["area"],
                                     "size": "xxs", "color": "#555555", "wrap": True},
                                ]},
                            ],
                        },
                        {"type": "separator"},
                        {"type": "text", "text": "\U0001f4b0 \u53f0\u7063\u4eba\u6700\u611b\u7528\u7684\u8a02\u623f\u5e73\u53f0",
                         "size": "sm", "color": "#999999", "margin": "md"},
                    ],
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "10px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#E91E8C", "height": "sm",
                         "action": {"type": "uri", "label": "\U0001f3e8 Agoda \u8a02\u98ef\u5e97", "uri": agoda}},
                        {"type": "button", "style": "primary", "color": "#003580", "height": "sm",
                         "action": {"type": "uri", "label": "\U0001f3e8 Booking.com", "uri": booking}},
                        {"type": "button", "style": "primary", "color": "#2577E3", "height": "sm",
                         "action": {"type": "uri", "label": "\U0001f3e8 Trip.com", "uri": trip_com}},
                        {"type": "separator", "margin": "md"},
                        {"type": "button", "style": "secondary", "height": "sm",
                         "action": {"type": "postback", "label": "\u2705 \u5df2\u770b\u904e\uff0c\u4e0b\u4e00\u6b65\uff1a\u884c\u7a0b",
                                    "data": "trip_step=6", "displayText": "\u7e7c\u7e8c\u898f\u5283\u884c\u7a0b"}},
                    ],
                },
            },
        },
        {
            "type": "text", "text":
                "\U0001f4a1 \u5c0f\u63d0\u793a\uff1a\n"
                "\u2022 \u5148\u700f\u89bd\u4ee5\u4e0a\u5e73\u53f0\u6bd4\u50f9\n"
                "\u2022 \u770b\u5b8c\u5f8c\u9ede\u300c\u5df2\u770b\u904e\uff0c\u4e0b\u4e00\u6b65\u300d\u7e7c\u7e8c\n"
                "\u2022 \u6216\u76f4\u63a5\u8f38\u5165\u4f60\u504f\u597d\u7684\u5340\u57df\uff08\u5982\u300c\u5e02\u4e2d\u5fc3\u300d\u300c\u8fd1\u8eca\u7ad9\u300d\uff09",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "\U0001f3d9\ufe0f \u5e02\u4e2d\u5fc3", "text": "\u5e02\u4e2d\u5fc3"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f689 \u8fd1\u8eca\u7ad9", "text": "\u8fd1\u8eca\u7ad9"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f4b0 \u4fbf\u5b9c\u512a\u5148", "text": "\u4fbf\u5b9c\u512a\u5148"}},
                    {"type": "action", "action": {"type": "postback", "label": "\u27a1\ufe0f \u8df3\u904e", "data": "trip_step=6", "displayText": "\u8df3\u904e\u4f4f\u5bbf"}},
                ],
            },
        },
    ]


def _step5_hotels(user_id: str, text: str) -> list:
    """步驟 5：記錄住宿偏好，進入步驟 6"""
    preference = text.strip()
    if preference:
        update_session(user_id, {"hotel_preference": preference}, step=6)
    else:
        update_session(user_id, {}, step=6)
    return _prompt_itinerary(user_id)


# ─── 步驟 6：行程大綱 ────────────────────────────────

def _prompt_itinerary(user_id: str) -> list:
    session = get_session(user_id) or {}
    city = session.get("destination_name", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")

    days = _calc_days(depart, ret)
    days_text = f"{days} \u5929" if days > 0 else "\u5f48\u6027\u5929\u6578"

    return [{
        "type": "text", "text":
            f"[6/8] \u884c\u7a0b\u5927\u7db1\n\n"
            f"\u76ee\u7684\u5730\uff1a{city}\n"
            f"\u5929\u6578\uff1a{days_text}\n\n"
            f"\u6709\u6c92\u6709\u7279\u5225\u60f3\u53bb\u7684\u666f\u9ede\u6216\u60f3\u907f\u958b\u7684\uff1f\n\n"
            f"\u53ef\u4ee5\u544a\u8a34\u6211\uff0c\u4f8b\u5982\uff1a\n"
            f"\u2022 \u300c\u60f3\u53bb\u8fea\u58eb\u5c3c\u300d\n"
            f"\u2022 \u300c\u60f3\u9003\u907f\u89c0\u5149\u5ba2\u300d\n"
            f"\u2022 \u300c\u7f8e\u98df\u70ba\u4e3b\u300d\n\n"
            f"\u6216\u9ede\u300c\u5e6b\u6211\u898f\u5283\u300d\u7531\u6211\u81ea\u52d5\u5b89\u6392",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "\U0001f3f0 \u71b1\u9580\u666f\u9ede", "text": "\u71b1\u9580\u666f\u9ede"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f35c \u7f8e\u98df\u70ba\u4e3b", "text": "\u7f8e\u98df\u70ba\u4e3b"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f6cd\ufe0f \u8cfc\u7269\u884c\u7a0b", "text": "\u8cfc\u7269\u884c\u7a0b"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f916 \u5e6b\u6211\u898f\u5283", "text": "\u5e6b\u6211\u898f\u5283"}},
            ],
        },
    }]


def _step6_itinerary(user_id: str, text: str) -> list:
    update_session(user_id, {"custom_requests": text.strip()}, step=7)
    return _prompt_travel_info(user_id)


# ─── 步驟 7：行前須知 ────────────────────────────────

def _prompt_travel_info(user_id: str) -> list:
    """產出完整行前須知（簽證+海關+文化+天氣+匯率+打包）"""
    from bot.services.travel_data import get_visa_info, get_customs_info, get_cultural_notes, get_packing_list
    from bot.services.weather_api import get_weather
    from bot.services.exchange_api import get_exchange_rate
    from bot.constants.countries import COUNTRY_CURRENCY, COUNTRY_NAME
    from bot.flex.progress_bar import build_progress_bar

    session = get_session(user_id) or {}
    country = session.get("country_code", "")
    city = session.get("destination_name", "")
    dest = session.get("destination_code", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    country_name = COUNTRY_NAME.get(country, city)

    bubbles = []

    # ── Bubble 1: 簽證 ──
    visa = get_visa_info(country)
    if visa:
        visa_status = "\u2705 \u514d\u7c3d" if visa.get("visa_required") is False else f"\u26a0\ufe0f {visa.get('visa_required', '\u9700\u7c3d\u8b49')}"
        visa_text = (
            f"{visa_status}\n"
            f"\u505c\u7559\uff1a{visa.get('stay_limit', 'N/A')}\n"
            f"\u8b77\u7167\uff1a{visa.get('passport_validity', 'N/A')}\n"
            f"\u5099\u8a3b\uff1a{visa.get('notes', '')}"
        )
        bubbles.append(_info_bubble("\U0001f4d8 \u7c3d\u8b49\u8cc7\u8a0a", visa_text, "#1565C0"))

    # ── Bubble 2: 海關禁品 ──
    customs = get_customs_info(country)
    if customs:
        prohibited = customs.get("prohibited_in", [])
        duty_free = customs.get("duty_free", {})
        important = customs.get("important", [])

        customs_lines = ["\u274c \u7981\u6b62\u651c\u5e36\u5165\u5883\uff1a"]
        for item in prohibited[:5]:
            customs_lines.append(f"  \u2022 {item}")
        if duty_free:
            customs_lines.append("\n\u2705 \u514d\u7a05\u984d\u5ea6\uff1a")
            for k, v in list(duty_free.items())[:4]:
                customs_lines.append(f"  \u2022 {k}: {v}")
        if important:
            warnings = important if isinstance(important, list) else [important]
            for w in warnings[:2]:
                customs_lines.append(f"\n\u26a0\ufe0f {w}")

        bubbles.append(_info_bubble("\U0001f6c3 \u6d77\u95dc\u7981\u54c1", "\n".join(customs_lines), "#E53935"))

    # ── Bubble 3: 文化注意事項 ──
    culture = get_cultural_notes(country)
    if culture:
        tips = culture.get("tips", [])
        culture_lines = []
        for tip in tips[:6]:
            culture_lines.append(f"\u2022 {tip}")
        if culture.get("plug_type"):
            culture_lines.append(f"\n\U0001f50c \u63d2\u5ea7\uff1a{culture['plug_type']}")
        if culture.get("payment"):
            culture_lines.append(f"\U0001f4b3 {culture['payment']}")
        if culture.get("transport_tip"):
            culture_lines.append(f"\U0001f689 {culture['transport_tip']}")

        bubbles.append(_info_bubble("\U0001f30d \u6587\u5316\u5c0f\u63d0\u9192", "\n".join(culture_lines), "#6A1B9A"))

    # ── Bubble 4: 天氣 ──
    weather = get_weather(dest, depart, ret) if depart else None
    if weather:
        weather_text = (
            f"\U0001f321\ufe0f \u6e29\u5ea6\uff1a{weather['avg_low']}\u00b0C ~ {weather['avg_high']}\u00b0C\n"
            f"\U0001f327\ufe0f \u964d\u96e8\u6a5f\u7387\uff1a{weather['rain_chance']}%\n"
            f"\U0001f4ac {weather['description']}"
        )
        bubbles.append(_info_bubble("\u2600\ufe0f \u5929\u6c23\u9810\u5831", weather_text, "#FF9800"))

    # ── Bubble 5: 匯率 ──
    currency_code = COUNTRY_CURRENCY.get(country, "")
    exchange = get_exchange_rate(currency_code) if currency_code else None
    if exchange:
        exchange_text = (
            f"\U0001f4b1 {exchange['display']}\n"
            f"\U0001f4b0 {exchange['example']}\n"
            f"\U0001f4c5 \u8cc7\u6599\u65e5\u671f\uff1a{exchange.get('date', 'N/A')}"
        )
        bubbles.append(_info_bubble("\U0001f4b1 \u532f\u7387\u8cc7\u8a0a", exchange_text, "#2E7D32"))

    # ── Bubble 6: 打包清單 ──
    month = int(depart[5:7]) if depart and len(depart) >= 7 else 6
    packing = get_packing_list(country, month)
    if packing:
        pack_lines = ["\U0001f4c4 \u8b49\u4ef6\uff1a"]
        for item in packing["documents"][:4]:
            pack_lines.append(f"  \u2610 {item}")
        if packing["climate_items"]:
            pack_lines.append(f"\n\U0001f321\ufe0f {packing['climate_label']}\uff1a")
            for item in packing["climate_items"][:4]:
                pack_lines.append(f"  \u2610 {item}")
        if packing["country_items"]:
            pack_lines.append(f"\n\U0001f1f9\U0001f1fc {country_name}\u5c08\u7528\uff1a")
            for item in packing["country_items"][:4]:
                pack_lines.append(f"  \u2610 {item}")

        bubbles.append(_info_bubble("\U0001f9f3 \u6253\u5305\u6e05\u55ae", "\n".join(pack_lines), "#5C6BC0"))

    # 如果什麼資料都沒有
    if not bubbles:
        return [{
            "type": "text", "text":
                f"[7/8] \u884c\u524d\u9808\u77e5\n\n"
                f"\u62b1\u6b49\uff0c\u76ee\u524d\u9084\u6c92\u6709 {city} \u7684\u8a73\u7d30\u884c\u524d\u8cc7\u8a0a\u3002\n"
                f"\u5efa\u8b70\u4f60\u67e5\u8a62\u5916\u4ea4\u90e8\u9818\u4e8b\u4e8b\u52d9\u5c40\u7db2\u7ad9\u3002",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "postback", "label": "\u27a1\ufe0f \u4e0b\u4e00\u6b65", "data": "trip_step=8", "displayText": "\u7e7c\u7e8c"}},
                ],
            },
        }]

    messages = [
        {"type": "text", "text":
            f"[7/8] \u884c\u524d\u9808\u77e5\n\n"
            f"\u4ee5\u4e0b\u662f {city}({country_name}) \u7684\u91cd\u8981\u884c\u524d\u8cc7\u8a0a\uff1a\n"
            f"\u2190 \u5de6\u53f3\u6ed1\u52d5\u67e5\u770b\u5168\u90e8"},
        {
            "type": "flex",
            "altText": f"{city} \u884c\u524d\u9808\u77e5",
            "contents": {"type": "carousel", "contents": bubbles},
        },
        {
            "type": "text", "text":
                "\u26a0\ufe0f \u4ee5\u4e0a\u8cc7\u8a0a\u50c5\u4f9b\u53c3\u8003\uff0c\u8acb\u4ee5\u5404\u570b\u5b98\u65b9\u516c\u544a\u70ba\u6e96\u3002\n\n"
                "\u9ede\u300c\u4e0b\u4e00\u6b65\u300d\u7522\u51fa\u5b8c\u6574\u8a08\u756b\u66f8\uff01",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "postback", "label": "\u27a1\ufe0f \u7522\u51fa\u8a08\u756b\u66f8", "data": "trip_step=8", "displayText": "\u7522\u51fa\u8a08\u756b\u66f8"}},
                ],
            },
        },
    ]

    return messages


def _info_bubble(title: str, content: str, color: str) -> dict:
    """通用資訊卡片"""
    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": color, "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": title, "color": "#FFFFFF", "weight": "bold", "size": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "sm",
            "contents": [
                {"type": "text", "text": content, "size": "sm", "color": "#444444", "wrap": True},
            ],
        },
    }


def _step7_travel_info(user_id: str, text: str) -> list:
    update_session(user_id, {}, step=8)
    # 行程大綱 + 計畫書合併輸出
    from bot.utils.itinerary_builder import build_itinerary_flex
    session = get_session(user_id) or {}
    dest = session.get("destination_code", "")
    city = session.get("destination_name", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    _budget_num = session.get("budget", 0)
    budget = f"NT${_budget_num//10000}萬" if _budget_num else ""
    adults = session.get("adults", 1)
    itinerary_msgs = build_itinerary_flex(dest, depart, ret, city, budget=budget, adults=adults) if dest and depart else []
    summary_msgs = _prompt_summary(user_id)
    return (itinerary_msgs + summary_msgs)[:5]


# ─── 步驟 8：完整計畫書（Phase 5 完整實作）───────────

def _prompt_summary(user_id: str) -> list:
    """產出完整計畫書"""
    from bot.constants.cities import IATA_TO_NAME, TW_AIRPORTS, CITY_FLAG, IATA_TO_COUNTRY
    from bot.constants.airlines import airline_name
    from bot.constants.countries import COUNTRY_NAME, COUNTRY_CURRENCY
    from bot.services.travel_data import get_visa_info, get_customs_info, get_cultural_notes
    from bot.services.weather_api import get_weather
    from bot.services.exchange_api import get_exchange_rate
    from bot.flex.progress_bar import build_progress_bar
    from bot.utils.url_builder import skyscanner_url, google_flights_url, agoda_url, booking_url

    session = get_session(user_id) or {}
    city = session.get("destination_name", "\u672a\u8a2d\u5b9a")
    dest = session.get("destination_code", "")
    origin = session.get("origin", "TPE")
    country = session.get("country_code", "")
    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    date_display = _format_dates(session)
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    adults = session.get("adults", 1)
    budget = session.get("budget", 0)
    hotel_pref = session.get("hotel_preference", "")
    custom = session.get("custom_requests", "")
    flag = CITY_FLAG.get(dest, "\u2708\ufe0f")
    days = _calc_days(depart, ret)
    days_text = f"{days}\u5929{days-1}\u591c" if days > 1 else "\u5f48\u6027\u5929\u6578"
    country_name = COUNTRY_NAME.get(country, "")

    # 機票資訊
    flight_choice = session.get("flight_choice")
    flight_results = session.get("flight_results", [])
    if flight_choice:
        flight_text = f"NT${flight_choice.get('price', 0):,} ({airline_name(flight_choice.get('airline', ''))})"
    elif flight_results:
        f = flight_results[0]
        flight_text = f"NT${f.get('price', 0):,} ({airline_name(f.get('airline', ''))})"
    else:
        flight_text = "\u5c1a\u672a\u9078\u64c7"

    # 簽證摘要
    visa = get_visa_info(country)
    visa_text = ""
    if visa:
        visa_text = "\u2705 \u514d\u7c3d" if visa.get("visa_required") is False else f"\u26a0\ufe0f {visa.get('visa_required')}"
        visa_text += f"({visa.get('stay_limit', '')})"

    # 天氣摘要
    weather = get_weather(dest, depart, ret) if depart else None
    weather_text = ""
    if weather:
        weather_text = f"{weather['avg_low']}-{weather['avg_high']}\u00b0C, \u964d\u96e8{weather['rain_chance']}%"

    # 匯率摘要
    currency_code = COUNTRY_CURRENCY.get(country, "")
    exchange = get_exchange_rate(currency_code) if currency_code else None
    exchange_text = exchange["example"] if exchange else ""

    # 文化摘要
    culture = get_cultural_notes(country)
    culture_highlights = ""
    if culture:
        plug = culture.get("plug_type", "")
        culture_highlights = f"\U0001f50c {plug}" if plug else ""

    # ── 建立計畫書 Flex Message ──
    # 摘要卡片
    summary_body = [
        {"type": "text", "text": f"{flag} {city} {days_text}", "weight": "bold", "size": "lg"},
        {"type": "separator", "margin": "md"},
        _summary_row("\u2708\ufe0f \u8def\u7dda", f"{origin_name} \u2192 {city}"),
        _summary_row("\U0001f4c5 \u65e5\u671f", date_display),
        _summary_row("\U0001f465 \u4eba\u6578", f"{adults} \u4eba"),
        _summary_row("\U0001f4b0 \u9810\u7b97", f"NT${budget:,}"),
        {"type": "separator", "margin": "md"},
        _summary_row("\u2708\ufe0f \u6a5f\u7968", flight_text),
        _summary_row("\U0001f3e8 \u4f4f\u5bbf", hotel_pref or "\u672a\u8a2d\u5b9a"),
    ]

    if visa_text:
        summary_body.append(_summary_row("\U0001f4d8 \u7c3d\u8b49", visa_text))
    if weather_text:
        summary_body.append(_summary_row("\u2600\ufe0f \u5929\u6c23", weather_text))
    if exchange_text:
        summary_body.append(_summary_row("\U0001f4b1 \u532f\u7387", exchange_text))
    if culture_highlights:
        summary_body.append(_summary_row("\U0001f50c \u63d2\u5ea7", culture_highlights))
    if custom:
        summary_body.append({"type": "separator", "margin": "md"})
        summary_body.append(_summary_row("\U0001f4dd \u5099\u8a3b", custom))

    summary_body.append({"type": "separator", "margin": "md"})
    summary_body.append({
        "type": "text", "text": "\u26a0\ufe0f \u7c3d\u8b49/\u6d77\u95dc\u8cc7\u8a0a\u50c5\u4f9b\u53c3\u8003\uff0c\u8acb\u4ee5\u5b98\u65b9\u516c\u544a\u70ba\u6e96",
        "size": "xxs", "color": "#999999", "wrap": True, "margin": "md",
    })
    summary_body.append({"type": "separator", "margin": "md"})
    summary_body.append({
        "type": "text",
        "text": "\u2b06\ufe0f \u8a08\u756b\u66f8\u4e0a\u65b9\u9084\u6709\uff1a\u5929\u5929\u884c\u7a0b\u5361\u7247\u00b7\u884c\u524d\u9808\u77e5\uff0c\u5de6\u53f3\u6ed1\u52d5\u67e5\u770b",
        "size": "xs", "color": "#E91E63", "weight": "bold", "wrap": True, "margin": "sm",
    })

    # 訂票連結
    footer_buttons = []
    if dest and depart:
        footer_buttons.append({
            "type": "button", "style": "primary", "color": "#00B0F0", "height": "sm",
            "action": {"type": "uri", "label": "\U0001f50d \u53bb Skyscanner \u8a02\u7968",
                       "uri": skyscanner_url(origin, dest, depart, ret)},
        })
        from bot.constants.cities import AGODA_CITY_KEYWORDS
        city_kw = AGODA_CITY_KEYWORDS.get(dest, city)
        footer_buttons.append({
            "type": "button", "style": "primary", "color": "#E91E8C", "height": "sm",
            "action": {"type": "uri", "label": "\U0001f3e8 \u53bb Agoda \u8a02\u623f",
                       "uri": agoda_url(city_kw, depart, ret)},
        })

    # 產生下載 token，存行程資料到 Redis（72 小時）
    import uuid
    from bot.services.redis_store import redis_set
    from bot.config import LINE_CHANNEL_ACCESS_TOKEN
    import json as _json

    download_token = uuid.uuid4().hex
    plan_data = {
        "flag": flag, "city": city, "days_text": days_text,
        "origin_name": origin_name, "date_display": date_display,
        "adults": adults, "budget": budget,
        "flight_text": flight_text,
        "hotel_pref": hotel_pref,
        "visa_text": visa_text,
        "weather_text": weather_text,
        "exchange_text": exchange_text,
        "plug_text": culture_highlights,
        "custom": custom,
        "must_eat": _get_must_eat(dest),
        "itinerary": _get_itinerary_for_download(dest, depart, ret),
    }
    redis_set(f"download:{download_token}", _json.dumps(plan_data, ensure_ascii=False), ttl=259200)

    # 取得 Vercel 部署 URL
    vercel_url = "https://abroad-uturn.vercel.app"
    download_url = f"{vercel_url}/api/download?token={download_token}"

    footer_buttons.append({
        "type": "button", "style": "secondary", "height": "sm",
        "action": {"type": "uri", "label": "📥 下載行程計畫書 (.docx)",
                   "uri": download_url},
    })
    footer_buttons.extend([
        {"type": "button", "style": "secondary", "height": "sm",
         "action": {"type": "message", "label": "🔄 重新規劃", "text": "開始規劃"}},
        {"type": "button", "style": "secondary", "height": "sm",
         "action": {"type": "message", "label": "🌍 探索其他目的地", "text": "便宜"}},
    ])

    # ── 預估支出 Bubble ──
    from bot.utils.budget_estimator import build_budget_bubble
    flight_price = 0
    if flight_choice:
        flight_price = flight_choice.get("price", 0)
    elif session.get("flight_results"):
        flight_price = session["flight_results"][0].get("price", 0)
    budget_bubble = None
    if dest and days > 0 and flight_price > 0:
        budget_bubble = build_budget_bubble(dest, city, days, adults, flight_price, flag)

    # 儲存回饋排程（回程後 D+1 push 滿意度問卷）
    if ret and dest:
        try:
            import json as _json
            from bot.services.redis_store import redis_set
            _feedback_data = _json.dumps({"city": city, "dest": dest, "return_date": ret, "days": days, "adults": adults})
            redis_set(f"feedback:{user_id}", _feedback_data, ttl=60 * 60 * 24 * 30)
        except Exception:
            pass

    # 清除 session（規劃完成）
    clear_session(user_id)

    msgs = [
        {
            "type": "flex",
            "altText": f"\u2705 {city} {days_text} \u51fa\u570b\u8a08\u756b\u66f8",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "18px",
                    "contents": [
                        build_progress_bar(8),
                        {"type": "text", "text": f"\U0001f389 \u4f60\u7684\u51fa\u570b\u8a08\u756b\u5b8c\u6210\uff01",
                         "color": "#FFFFFF", "weight": "bold", "size": "xl", "margin": "md"},
                        {"type": "text", "text": f"{flag} {city} {days_text}",
                         "color": "#FFE0CC", "size": "md", "margin": "xs"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": summary_body,
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "10px",
                    "contents": footer_buttons,
                },
            },
        },
    ]

    if budget_bubble:
        msgs.append({
            "type": "flex",
            "altText": f"💰 {city} 預估旅遊支出",
            "contents": budget_bubble,
        })

    return msgs


def _get_must_eat(dest_code: str) -> list:
    """取得目的地必吃清單（供下載用）"""
    try:
        from bot.utils.itinerary_builder import _get_template
        tmpl = _get_template(dest_code)
        return tmpl.get("must_eat", [])
    except Exception:
        return []


def _get_itinerary_for_download(dest_code: str, depart: str, ret: str) -> list:
    """取得天天行程資料（供下載用，純文字格式）"""
    try:
        import datetime
        from bot.utils.itinerary_builder import _get_template, _calc_days
        tmpl = _get_template(dest_code)
        if not tmpl:
            return []
        days = _calc_days(depart, ret)
        full_days = tmpl.get("full_days", [])
        result = []
        for day_num in range(1, days + 1):
            date_label = ""
            if depart:
                try:
                    d = datetime.date.fromisoformat(depart[:10])
                    actual = d + datetime.timedelta(days=day_num - 1)
                    date_label = f"{actual.month}/{actual.day}"
                except Exception:
                    pass
            if day_num == 1:
                plan = tmpl.get("arrival", {})
                title = f"Day {day_num} 抵達"
            elif day_num == days:
                plan = tmpl.get("departure", {})
                title = f"Day {day_num} 返台"
            else:
                idx = (day_num - 2) % max(len(full_days), 1)
                plan = full_days[idx] if full_days else {}
                title = f"Day {day_num} {plan.get('theme', '深度探索')}"
            result.append({
                "title": title,
                "date_label": date_label,
                "am": plan.get("am", ""),
                "pm": plan.get("pm", ""),
                "eve": plan.get("eve", ""),
            })
        return result
    except Exception:
        return []


def _summary_row(label: str, value: str) -> dict:
    return {
        "type": "box", "layout": "horizontal", "margin": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#888888", "flex": 3},
            {"type": "text", "text": value, "size": "sm", "color": "#333333", "flex": 7, "wrap": True},
        ],
    }


def _step8_summary(user_id: str, text: str) -> list:
    return _prompt_summary(user_id)


def _handle_selection(user_id: str, params: dict) -> list:
    """處理步驟內的選擇 postback"""
    select_type = params.get("trip_select", "")

    if select_type == "flight":
        # 使用者選了一個機票方案
        idx = int(params.get("idx", 0))
        price = params.get("price", "0")
        airline_code = params.get("airline", "")

        session = get_session(user_id) or {}
        flight_results = session.get("flight_results", [])
        chosen = flight_results[idx] if idx < len(flight_results) else {}

        from bot.constants.airlines import airline_name
        airline_display = airline_name(airline_code)

        update_session(user_id, {
            "flight_choice": chosen,
            "flight_choice_display": f"NT${int(price):,} ({airline_display})",
        }, step=5)

        return [
            {"type": "text", "text":
                f"\u2705 \u5df2\u9078\u64c7\u6a5f\u7968\uff1a{airline_display} NT${int(price):,}\n\n"
                f"\u63a5\u4e0b\u4f86\u5e6b\u4f60\u627e\u4f4f\u5bbf\uff01"
            },
        ] + _prompt_hotels(user_id)

    return [{"type": "text", "text": "\u5df2\u6536\u5230\u4f60\u7684\u9078\u64c7\uff01"}]


# ─── 工具函數 ────────────────────────────────────────

def _format_dates(session: dict) -> str:
    """格式化日期顯示"""
    flex = session.get("flexibility", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")

    if flex == "flexible":
        return "\u5f48\u6027\u65e5\u671f"
    elif flex == "month" and depart:
        return f"{depart[5:]}\u6708"
    elif depart and ret:
        d = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
        r = ret[5:].replace("-", "/") if len(ret) >= 10 else ret
        return f"{d} ~ {r}"
    elif depart:
        d = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
        return d
    return "\u672a\u8a2d\u5b9a"


def _calc_days(depart: str, ret: str) -> int:
    """計算旅行天數"""
    if not depart or not ret or len(depart) < 10 or len(ret) < 10:
        return 0
    try:
        import datetime
        d1 = datetime.date.fromisoformat(depart[:10])
        d2 = datetime.date.fromisoformat(ret[:10])
        return (d2 - d1).days + 1
    except Exception:
        return 0
