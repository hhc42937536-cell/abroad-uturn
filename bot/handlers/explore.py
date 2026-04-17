"""快速探索最便宜目的地（保留的獨立功能）"""

import datetime

from bot.config import TRAVELPAYOUTS_TOKEN
from bot.constants.cities import IATA_TO_NAME, TW_AIRPORTS, TW_ALL_AIRPORTS
from bot.services.travelpayouts import search_cheapest_by_month, search_cheapest_any
from bot.flex.flight_bubble import flight_bubble
from bot.flex.month_picker import month_picker_flex
from bot.utils.url_builder import google_explore_url, skyscanner_url, google_flights_url


def _no_flights_fallback(origin: str, dest_code: str = None, depart: str = None, ret: str = None) -> list:
    """即時票價無法取得時的替代訊息，附 affiliate 導流連結"""
    if dest_code and depart:
        sky_uri = skyscanner_url(origin, dest_code, depart, ret or "")
        gf_uri = google_flights_url(origin, dest_code, depart, ret or "")
    else:
        sky_uri = f"https://www.skyscanner.com.tw/transport/flights/{origin.lower()}/anywhere/?adultsv2=1&currency=TWD&locale=zh-TW"
        gf_uri = google_explore_url(origin)

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
                     "text": "API \u66ab\u6642\u7121\u56de\u61c9\uff0c\u8acb\u76f4\u63a5\u524d\u5f80\u8a02\u7968\u5e73\u53f0\u641c\u5c0b\u6700\u65b0\u7968\u50f9 \U0001f447",
                     "size": "sm", "color": "#888888", "wrap": True, "margin": "sm"},
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical", "paddingAll": "10px", "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#0770E3",
                     "action": {"type": "uri", "label": "\U0001f50d Skyscanner \u641c\u5c0b", "uri": sky_uri}},
                    {"type": "button", "style": "secondary",
                     "action": {"type": "uri", "label": "\u2708\ufe0f Google Flights / Explore", "uri": gf_uri}},
                ],
            },
        },
    }]


def _dedupe_flights(flights: list, limit: int = 10) -> list:
    seen = {}
    for f in flights:
        dest = f.get("destination", "")
        if not dest or dest in TW_ALL_AIRPORTS:
            continue
        if dest not in seen or f.get("price", 99999) < seen[dest].get("price", 99999):
            seen[dest] = f
    return sorted(seen.values(), key=lambda x: x.get("price", 99999))[:limit]


def _google_explore_bubble() -> dict:
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical",
            "justifyContent": "center", "alignItems": "center",
            "paddingAll": "20px", "spacing": "md",
            "contents": [
                {"type": "text", "text": "\U0001f310", "size": "3xl", "align": "center"},
                {"type": "text", "text": "\u60f3\u770b\u66f4\u591a\uff1f", "weight": "bold", "size": "lg", "align": "center"},
                {"type": "text", "text": "\u7528 Google \u63a2\u7d22\u5168\u7403\u6700\u4fbf\u5b9c\u76ee\u7684\u5730",
                 "size": "sm", "color": "#888888", "align": "center", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px", "spacing": "sm",
            "contents": [
                {"type": "button", "style": "primary", "color": "#4285F4",
                 "action": {"type": "uri", "label": "Google Travel Explore",
                            "uri": google_explore_url()}},
                {"type": "button", "style": "secondary",
                 "action": {"type": "message", "label": "\U0001f4c5 \u9078\u7279\u5b9a\u6708\u4efd\u63a2\u7d22",
                            "text": "\u63a2\u7d22\u6700\u4fbf\u5b9c"}},
            ],
        },
    }


def handle_explore_cheapest(origin: str = "TPE") -> list:
    """Google Explore 風格：直接顯示熱門航線最低參考價 + 月份/目的地搜尋入口"""
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_cheapest_any(origin)
    if not flights:
        return _no_flights_fallback(origin)

    unique = _dedupe_flights(flights, limit=8)
    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    explore_url = google_explore_url(origin)

    # 各目的地卡片
    bubbles = [flight_bubble(f, i) for i, f in enumerate(unique)]

    # 尾端：更多探索選單 bubble
    action_bubble = {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#4285F4", "paddingAll": "15px",
            "contents": [
                {"type": "text", "text": "🗺️ 更多探索", "color": "#FFFFFF",
                 "weight": "bold", "size": "lg"},
                {"type": "text", "text": "Google 全球地圖・選月份・熱門國家",
                 "color": "#FFFFFF99", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "12px",
            "contents": [
                {"type": "button", "style": "primary", "color": "#4285F4", "height": "sm",
                 "action": {"type": "uri",
                            "label": "🌐 Google Explore 全球價格地圖",
                            "uri": explore_url}},
                {"type": "button", "style": "secondary", "height": "sm",
                 "action": {"type": "message",
                            "label": "📅 選月份精選（指定月份最低價）",
                            "text": "選月份"}},
                {"type": "button", "style": "secondary", "height": "sm",
                 "action": {"type": "message",
                            "label": "🌍 熱門國家快選",
                            "text": "熱門國家"}},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "paddingAll": "10px", "spacing": "xs",
            "contents": [
                {"type": "text",
                 "text": "💡 直接輸入城市名＋日期也能查",
                 "size": "xs", "color": "#888888", "align": "center", "wrap": True},
                {"type": "text",
                 "text": "例：「東京 6/15-6/20」",
                 "size": "xs", "color": "#AAAAAA", "align": "center"},
            ],
        },
    }
    bubbles.append(action_bubble)

    return [
        {"type": "text",
         "text": (
             f"✈️ {origin_name} 出發・熱門航線最低參考價\n"
             "⚠️ 為歷史含稅低價參考，實際以訂票網站為準\n"
             "👉 滑動看更多目的地，最後一張可直連 Google Explore"
         )},
        {
            "type": "flex",
            "altText": f"✈️ {origin_name} 出發最便宜目的地",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def handle_quick_explore(origin: str = "TPE") -> list:
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_cheapest_any(origin)

    if not flights:
        return _no_flights_fallback(origin)

    unique = _dedupe_flights(flights)
    bubbles = [flight_bubble(f, i) for i, f in enumerate(unique)]
    bubbles.append(_google_explore_bubble())

    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    return [
        {"type": "text", "text": f"\u2708\ufe0f {origin_name}\u51fa\u767c\uff0c\u8fd1\u671f\u6700\u4fbf\u5b9c\u7684\u76ee\u7684\u5730\uff1a"},
        {
            "type": "flex",
            "altText": "\u8fd1\u671f\u6700\u4fbf\u5b9c\u76ee\u7684\u5730",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def handle_explore(month: str, origin: str = "TPE") -> list:
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_cheapest_by_month(origin, month)
    if not flights:
        return _no_flights_fallback(origin)

    unique = _dedupe_flights(flights)
    bubbles = [flight_bubble(f, i) for i, f in enumerate(unique)]
    bubbles.append({
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical",
            "justifyContent": "center", "alignItems": "center",
            "paddingAll": "20px", "spacing": "md",
            "contents": [
                {"type": "text", "text": "\U0001f310", "size": "3xl", "align": "center"},
                {"type": "text", "text": "\u60f3\u770b\u66f4\u591a\uff1f", "weight": "bold", "size": "lg", "align": "center"},
                {"type": "text", "text": "\u7528 Google \u63a2\u7d22\u5168\u7403\u6700\u4fbf\u5b9c\u76ee\u7684\u5730",
                 "size": "sm", "color": "#888888", "align": "center", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px",
            "contents": [
                {"type": "button", "style": "primary", "color": "#4285F4",
                 "action": {"type": "uri", "label": "Google Travel Explore",
                            "uri": google_explore_url()}},
            ],
        },
    })

    month_display = month[5:] if len(month) >= 7 else month
    return [{
        "type": "flex",
        "altText": f"{month_display}\u6708\u6700\u4fbf\u5b9c\u822a\u73ed",
        "contents": {"type": "carousel", "contents": bubbles},
    }]


def handle_direct_flights(origin: str = "TPE") -> list:
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_cheapest_any(origin, direct="true")
    if not flights:
        return _no_flights_fallback(origin)

    unique = _dedupe_flights(flights)
    bubbles = [flight_bubble(f, i) for i, f in enumerate(unique)]
    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    return [
        {"type": "text", "text": f"\u2708\ufe0f {origin_name}\u51fa\u767c\uff0c\u76f4\u98db\u76ee\u7684\u5730\u6700\u4f4e\u50f9\uff1a"},
        {"type": "flex", "altText": "\u76f4\u98db\u822a\u73ed", "contents": {"type": "carousel", "contents": bubbles}},
    ]


def handle_transfer_cheapest(origin: str = "TPE") -> list:
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_cheapest_any(origin)
    if not flights:
        return _no_flights_fallback(origin)

    transfer_flights = [f for f in flights if f.get("transfers", 0) > 0]
    if not transfer_flights:
        return [{"type": "text", "text": "\u76ee\u524d\u6240\u6709\u822a\u73ed\u90fd\u662f\u76f4\u98db\uff0c\u6c92\u6709\u66f4\u4fbf\u5b9c\u7684\u8f49\u6a5f\u9078\u9805 \u2708\ufe0f"}]

    unique = _dedupe_flights(transfer_flights)
    bubbles = [flight_bubble(f, i) for i, f in enumerate(unique)]
    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    return [
        {"type": "text", "text": f"\U0001f504 {origin_name}\u51fa\u767c\uff0c\u8f49\u6a5f\u8d85\u503c\u7968\uff08\u542b\u8f49\u6a5f\u66f4\u4fbf\u5b9c\uff09\uff1a"},
        {"type": "flex", "altText": "\u8f49\u6a5f\u6700\u7701", "contents": {"type": "carousel", "contents": bubbles}},
    ]


def handle_flexible_dates(text: str, origin: str = "TPE") -> list:
    from bot.utils.date_parser import parse_destination, parse_month
    from bot.services.travelpayouts import search_flights

    dest_code = parse_destination(text)
    month = parse_month(text)

    if not dest_code and not month:
        return [{"type": "text", "text":
            "\U0001f4c5 \u5f48\u6027\u65e5\u671f\u641c\u5c0b\n\n"
            "\u544a\u8a34\u6211\u76ee\u7684\u5730\u548c\u6708\u4efd\uff0c\u4f8b\u5982\uff1a\n"
            "\u300c\u6771\u4eac 6\u6708\u300d\n\u300c\u9996\u723e 7\u6708\u300d\n\u300c\u66fc\u8c37 8\u6708\u300d\n\n"
            "\u6211\u4f86\u5e6b\u4f60\u627e\u90a3\u500b\u6708\u6700\u4fbf\u5b9c\u7684\u5e7e\u5929\u51fa\u767c\uff01"
        }]
    if not dest_code:
        return [{"type": "text", "text": "\u8acb\u544a\u8a34\u6211\u76ee\u7684\u5730\uff0c\u4f8b\u5982\uff1a\n\u300c\u6771\u4eac 6\u6708\u300d\u300c\u9996\u723e 7\u6708\u300d"}]
    if not month:
        city_name = IATA_TO_NAME.get(dest_code, dest_code)
        return [{"type": "text", "text": f"\u8981\u53bb {city_name}\uff01\u8acb\u52a0\u4e0a\u6708\u4efd\uff0c\u4f8b\u5982\uff1a\n\u300c{city_name} 6\u6708\u300d"}]

    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_flights(origin, dest_code, month)
    if not flights:
        return [{"type": "text", "text":
            f"\u627e\u4e0d\u5230 {IATA_TO_NAME.get(dest_code, dest_code)} {month[5:]}\u6708\u7684\u822a\u73ed\u8cc7\u6599\uff0c\u8acb\u8a66\u8a66\u5176\u4ed6\u6708\u4efd \U0001f64f"
        }]

    seen = {}
    for f in flights:
        d = f.get("departure_at", "")[:10]
        if d and (d not in seen or f.get("price", 99999) < seen[d].get("price", 99999)):
            seen[d] = f
    sorted_flights = sorted(seen.values(), key=lambda x: x.get("price", 99999))[:6]

    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    bubbles = [flight_bubble(f, i) for i, f in enumerate(sorted_flights)]
    return [
        {"type": "text", "text": f"\U0001f4c5 {origin_name}\u2192{city_name} {month[5:]}\u6708\uff0c\u6700\u4fbf\u5b9c\u51fa\u767c\u65e5\uff1a"},
        {"type": "flex", "altText": f"{city_name} \u5f48\u6027\u65e5\u671f", "contents": {"type": "carousel", "contents": bubbles}},
    ]


def handle_compare(text: str, origin: str = "TPE") -> list:
    from bot.utils.date_parser import parse_destination, parse_date_range
    from bot.services.travelpayouts import search_flights

    dest_code = parse_destination(text)
    if not dest_code:
        return [{"type": "text", "text":
            "\u8acb\u544a\u8a34\u6211\u76ee\u7684\u5730\u548c\u65e5\u671f\uff0c\u4f8b\u5982\uff1a\n"
            "\u300c\u6771\u4eac 6/15-6/20\u300d\n\u300c\u9996\u723e 7\u670810\u523020\u300d\n"
            "\u300c\u66fc\u8c37 2026-08-01~2026-08-07\u300d\n\n"
            "\U0001f4a1 \u652f\u63f4\u7684\u76ee\u7684\u5730\uff1a\u65e5\u672c\u3001\u97d3\u570b\u3001\u6771\u5357\u4e9e\u3001\u6e2f\u6fb3\u3001\u6b50\u7f8e\u7b49 50+ \u57ce\u5e02"
        }]

    depart, ret = parse_date_range(text)
    if not depart:
        city_name = IATA_TO_NAME.get(dest_code, dest_code)
        return [{"type": "text", "text":
            f"\u76ee\u7684\u5730\uff1a{city_name} ({dest_code}) \u2705\n\n"
            f"\u8acb\u518d\u544a\u8a34\u6211\u65e5\u671f\uff0c\u4f8b\u5982\uff1a\n\u300c{city_name} 6/15-6/20\u300d"
        }]

    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_flights(origin, dest_code, depart, ret)
    if not flights:
        return _no_flights_fallback(origin, dest_code, depart, ret)

    flights.sort(key=lambda x: x.get("price", 99999))
    top = flights[:6]
    bubbles = [flight_bubble(f, i) for i, f in enumerate(top)]

    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    d_short = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
    r_short = ret[5:].replace("-", "/") if ret and len(ret) >= 10 else ""
    date_text = f"{d_short}" + (f"~{r_short}" if r_short else "")

    return [{
        "type": "flex",
        "altText": f"{city_name} {date_text} \u6a5f\u7968\u6bd4\u50f9",
        "contents": {"type": "carousel", "contents": bubbles},
    }]


def handle_package(text: str, origin: str = "TPE") -> list:
    from bot.utils.date_parser import parse_destination, parse_date_range
    from bot.services.travelpayouts import search_flights
    from bot.constants.cities import AGODA_CITY_KEYWORDS
    from bot.utils.url_builder import agoda_url, booking_url

    dest_code = parse_destination(text)
    depart, ret = parse_date_range(text)

    if not dest_code:
        return [{"type": "text", "text":
            "\U0001f3e8 \u6a5f\u52a0\u9152\u641c\u5c0b\n\n"
            "\u544a\u8a34\u6211\u76ee\u7684\u5730\u548c\u65e5\u671f\uff0c\u4f8b\u5982\uff1a\n"
            "\u300c\u6a5f\u52a0\u9152 \u6771\u4eac 6/15-6/20\u300d\n"
            "\u300c\u6a5f\u52a0\u9152 \u9996\u723e 7/10~7/14\u300d\n\n"
            "\u6211\u4f86\u5e6b\u4f60\u627e\u6a5f\u7968\uff0c\u9806\u4fbf\u9023\u7d50\u98ef\u5e97\u641c\u5c0b\uff01"
        }]

    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    city_kw = AGODA_CITY_KEYWORDS.get(dest_code, city_name)

    flights = None
    if TRAVELPAYOUTS_TOKEN and depart:
        flights = search_flights(origin, dest_code, depart, ret)
    agoda = agoda_url(city_kw, depart, ret)
    booking = booking_url(city_kw)

    messages = []
    if flights:
        flights.sort(key=lambda x: x.get("price", 99999))
        bubbles = [flight_bubble(f, i, show_track_btn=False) for i, f in enumerate(flights[:5])]
        origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
        messages += [
            {"type": "text", "text": f"\u2708\ufe0f {origin_name}\u2192{city_name} \u6a5f\u7968\uff1a"},
            {"type": "flex", "altText": f"{city_name} \u6a5f\u7968", "contents": {"type": "carousel", "contents": bubbles}},
        ]
    else:
        messages.append({"type": "text", "text": f"\u2708\ufe0f {city_name} \u6a5f\u7968\u8acb\u8f38\u5165\u65e5\u671f\u5f8c\u641c\u5c0b\uff0c\u4f8b\u5982\uff1a\n\u300c\u6a5f\u52a0\u9152 {city_name} 6/15-6/20\u300d"})

    messages.append({
        "type": "flex",
        "altText": f"{city_name} \u98ef\u5e97\u641c\u5c0b",
        "contents": {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E8C", "paddingAll": "15px",
                "contents": [
                    {"type": "text", "text": f"\U0001f3e8 {city_name} \u98ef\u5e97\u641c\u5c0b", "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "15px",
                "contents": [
                    {"type": "text", "text": "\u6a5f\u7968\u8a02\u597d\u5f8c\u5225\u5fd8\u4e86\u8a02\u98ef\u5e97\uff01", "size": "sm", "color": "#555555", "wrap": True},
                    {"type": "text", "text": "\u53f0\u7063\u4eba\u6700\u5e38\u7528\u7684\u5169\u500b\u98ef\u5e97\u5e73\u53f0\uff1a", "size": "sm", "color": "#888888", "margin": "sm"},
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "10px",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#E91E8C", "height": "sm",
                     "action": {"type": "uri", "label": "\U0001f3e8 Agoda \u8a02\u98ef\u5e97", "uri": agoda}},
                    {"type": "button", "style": "primary", "color": "#003580", "height": "sm",
                     "action": {"type": "uri", "label": "\U0001f3e8 Booking.com \u8a02\u98ef\u5e97", "uri": booking}},
                ],
            },
        },
    })
    return messages


def handle_popular_countries(origin: str = "TPE") -> list:
    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    regions = [
        ("\U0001f1ef\U0001f1f5 \u65e5\u672c", "#E53935", [
            ("\u6771\u4eac", "\u4fbf\u5b9c \u6771\u4eac"), ("\u5927\u962a", "\u4fbf\u5b9c \u5927\u962a"),
            ("\u798f\u5ca1", "\u4fbf\u5b9c \u798f\u5ca1"), ("\u672d\u5e4c", "\u4fbf\u5b9c \u672d\u5e4c"),
            ("\u6c96\u7e69", "\u4fbf\u5b9c \u6c96\u7e69"), ("\u540d\u53e4\u5c4b", "\u4fbf\u5b9c \u540d\u53e4\u5c4b"),
        ]),
        ("\U0001f1f0\U0001f1f7 \u97d3\u570b", "#1565C0", [
            ("\u9996\u723e", "\u4fbf\u5b9c \u9996\u723e"), ("\u91dc\u5c71", "\u4fbf\u5b9c \u91dc\u5c71"),
        ]),
        ("\U0001f30f \u6771\u5357\u4e9e", "#2E7D32", [
            ("\u6cf0\u570b \u66fc\u8c37", "\u4fbf\u5b9c \u66fc\u8c37"), ("\u65b0\u52a0\u5761", "\u4fbf\u5b9c \u65b0\u52a0\u5761"),
            ("\u5df4\u91cc\u5cf6", "\u4fbf\u5b9c \u5df4\u91cc\u5cf6"), ("\u8d8a\u5357 \u80e1\u5fd7\u660e", "\u4fbf\u5b9c \u80e1\u5fd7\u660e"),
            ("\u99ac\u4f86\u897f\u4e9e", "\u4fbf\u5b9c \u5409\u9686\u5761"), ("\u83f2\u5f8b\u8cd3", "\u4fbf\u5b9c \u99ac\u5c3c\u62c9"),
        ]),
        ("\U0001f1e8\U0001f1f3 \u6e2f\u6fb3\u4e2d\u570b", "#6A1B9A", [
            ("\u9999\u6e2f", "\u4fbf\u5b9c \u9999\u6e2f"), ("\u6fb3\u9580", "\u4fbf\u5b9c \u6fb3\u9580"),
            ("\u4e0a\u6d77", "\u4fbf\u5b9c \u4e0a\u6d77"), ("\u5317\u4eac", "\u4fbf\u5b9c \u5317\u4eac"),
        ]),
    ]

    bubbles = []
    for region_name, color, destinations in regions:
        btn_contents = []
        for label, msg in destinations:
            btn_contents.append({
                "type": "button", "style": "secondary", "height": "sm",
                "action": {"type": "message", "label": label, "text": msg},
            })
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": color, "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": region_name,
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": f"{origin_name}\u51fa\u767c\u30fb\u9ede\u9078\u67e5\u4f4e\u50f9",
                     "color": "#FFFFFF88", "size": "xs", "margin": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": btn_contents,
            },
        })

    return [
        {"type": "text", "text": f"\U0001f30d \u71b1\u9580\u76ee\u7684\u5730\u5feb\u9078\uff08{origin_name}\u51fa\u767c\uff09\n\u9ede\u9078\u76ee\u7684\u5730\u67e5\u6700\u4f4e\u7968\u50f9 \u2708\ufe0f"},
        {"type": "flex", "altText": "\u71b1\u9580\u570b\u5bb6\u5feb\u9078",
         "contents": {"type": "carousel", "contents": bubbles}},
    ]
