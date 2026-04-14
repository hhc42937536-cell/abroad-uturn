"""行程大綱生成器（靜態範本）

根據目的地 + 天數，自動組合 Day 1 ~ Day N 的行程大綱，
輸出為 LINE Flex Bubble（可放進 Carousel 或單獨回覆）。
"""

import json
import os
import datetime

_data_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data"
)
_cache = {}

# IATA → 範本 key 對照（多個 IATA 可對應同一城市）
_IATA_MAP = {
    # 日本
    "TYO": "TYO", "NRT": "TYO", "HND": "TYO",
    "OSA": "OSA", "KIX": "OSA", "ITM": "OSA",
    "OKA": "OKA",
    "FUK": "OSA",   # 福岡先用大阪模板（可之後補充）
    "NGO": "TYO",   # 名古屋先用東京模板
    "SPK": "TYO",   # 札幌先用東京模板
    # 韓國
    "SEL": "SEL", "ICN": "SEL", "GMP": "SEL",
    "PUS": "PUS",
    # 東南亞
    "BKK": "BKK", "DMK": "BKK",
    "SIN": "SIN",
    "SGN": "SGN", "HAN": "SGN",
    # 香港
    "HKG": "HKG",
    # 沖繩
}


def _load_templates() -> dict:
    if "itinerary" in _cache:
        return _cache["itinerary"]
    try:
        path = os.path.join(_data_dir, "itinerary_templates.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["itinerary"] = data
        return data
    except Exception as e:
        print(f"[itinerary] Load error: {e}")
        return {}


def _get_template(dest_code: str) -> dict:
    templates = _load_templates()
    key = _IATA_MAP.get(dest_code, dest_code)
    return templates.get(key) or templates.get("_default") or {}


def _calc_days(depart: str, ret: str) -> int:
    try:
        d1 = datetime.date.fromisoformat(depart[:10])
        d2 = datetime.date.fromisoformat(ret[:10])
        return max(1, (d2 - d1).days + 1)
    except Exception:
        return 3


def _day_bubble(day_num: int, label: str, plan: dict, depart_date: str = "") -> dict:
    """單天行程 Flex Bubble"""
    # 計算日期顯示
    date_label = ""
    if depart_date:
        try:
            d = datetime.date.fromisoformat(depart_date[:10])
            actual = d + datetime.timedelta(days=day_num - 1)
            date_label = f"  {actual.month}/{actual.day}"
        except Exception:
            pass

    header_color = "#FF6B35" if day_num == 1 else (
        "#1565C0" if day_num % 2 == 0 else "#2E7D32"
    )

    rows = []
    if plan.get("am"):
        rows.append(_time_row("🌅 上午", plan["am"]))
    if plan.get("pm"):
        rows.append(_time_row("☀️ 下午", plan["pm"]))
    if plan.get("eve"):
        rows.append(_time_row("🌙 晚上", plan["eve"]))

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_color, "paddingAll": "12px",
            "contents": [
                {"type": "text",
                 "text": f"Day {day_num}{date_label}",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
                {"type": "text",
                 "text": label,
                 "color": "#FFFFFFCC", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "12px",
            "contents": rows or [
                {"type": "text", "text": "彈性安排，依當天狀況調整",
                 "size": "sm", "color": "#888888"}
            ],
        },
    }


def _time_row(time_label: str, content: str) -> dict:
    return {
        "type": "box", "layout": "vertical", "margin": "sm",
        "contents": [
            {"type": "text", "text": time_label,
             "size": "xs", "color": "#888888", "weight": "bold"},
            {"type": "text", "text": content,
             "size": "sm", "color": "#333333", "wrap": True, "margin": "xs"},
        ],
    }


def build_itinerary_flex(dest_code: str, depart_date: str, return_date: str,
                         city_name: str = "", custom_requests: str = "") -> list:
    """
    生成行程大綱 Flex Carousel（1 則訊息）
    回傳 list[dict]，可直接 append 到 messages。
    """
    tmpl = _get_template(dest_code)
    if not tmpl:
        return []

    days = _calc_days(depart_date, return_date)
    display_city = city_name or tmpl.get("city_name", dest_code)
    must_eat = tmpl.get("must_eat", [])
    full_day_templates = tmpl.get("full_days", [])

    bubbles = []

    for day_num in range(1, days + 1):
        if day_num == 1:
            plan = tmpl.get("arrival", {})
            label = f"抵達 {display_city}"
        elif day_num == days:
            plan = tmpl.get("departure", {})
            label = "歸途 · 返台"
        else:
            idx = (day_num - 2) % max(len(full_day_templates), 1)
            plan = full_day_templates[idx] if full_day_templates else {}
            label = plan.get("theme", f"深度探索")

        bubbles.append(_day_bubble(day_num, label, plan, depart_date))

    # 最後加一張「必吃清單」bubble
    if must_eat:
        eat_lines = [{"type": "text", "text": f"• {item}",
                      "size": "sm", "color": "#555555", "wrap": True}
                     for item in must_eat[:6]]
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E63", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": f"🍜 {display_city} 必吃清單",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "出發前先記起來！",
                     "color": "#FFFFFF99", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "xs", "paddingAll": "12px",
                "contents": eat_lines,
            },
        })

    if not bubbles:
        return []

    return [
        {"type": "text",
         "text": f"📅 {display_city} {days}天行程大綱\n← 左右滑動看每天安排"},
        {
            "type": "flex",
            "altText": f"{display_city} {days}天行程大綱",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]
