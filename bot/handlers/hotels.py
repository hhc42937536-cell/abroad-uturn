"""格5：住宿推薦獨立入口"""

from bot.constants.cities import IATA_TO_NAME, AGODA_CITY_KEYWORDS, CITY_FLAG
from bot.utils.date_parser import parse_destination, parse_date_range
from bot.utils.url_builder import agoda_url, booking_url


def handle_hotels(text: str, user_id: str = "") -> list:
    """獨立住宿搜尋入口"""
    # 解析目的地
    clean = text.replace("住宿", "").replace("飯店", "").replace("推薦", "").strip()

    if not clean:
        return [{
            "type": "flex",
            "altText": "\U0001f3e8 \u4f4f\u5bbf\u63a8\u85a6",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#E91E8C", "paddingAll": "18px",
                    "contents": [
                        {"type": "text", "text": "\U0001f3e8 \u4f4f\u5bbf\u63a8\u85a6",
                         "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                        {"type": "text",
                         "text": "Agoda \u30fbBooking.com \u30fbTrip.com \u30fbGoogle Hotels",
                         "color": "#FCE4EC", "size": "sm", "margin": "sm", "wrap": True},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "md", "paddingAll": "18px",
                    "contents": [
                        {"type": "text", "text": "\U0001f4ac \u544a\u8a34\u6211\u76ee\u7684\u5730\uff0c\u4e00\u9375\u591a\u5e73\u53f0\u6bd4\u50f9\uff1a",
                         "weight": "bold", "size": "sm"},
                        {
                            "type": "box", "layout": "vertical", "spacing": "xs",
                            "backgroundColor": "#FFF0F5", "paddingAll": "12px",
                            "cornerRadius": "8px",
                            "contents": [
                                {"type": "text", "text": "\u2022 \u4f4f\u5bbf \u6771\u4eac", "size": "sm", "color": "#C2185B"},
                                {"type": "text", "text": "\u2022 \u98ef\u5e97 \u66fc\u8c37 6/15-6/20", "size": "sm", "color": "#C2185B"},
                                {"type": "text", "text": "\u2022 \u4f4f\u5bbf \u9996\u723e \u4e0b\u500b\u6708", "size": "sm", "color": "#C2185B"},
                            ],
                        },
                        {"type": "separator"},
                        {"type": "text", "text": "\U0001f4a1 \u5c0f\u6280\u5de7\uff1a\nAgoda \u5e38\u6709\u4eca\u65e5\u7279\u50f9\u3001Booking.com \u53ef\u514d\u8cbb\u53d6\u6d88",
                         "size": "xs", "color": "#999999", "wrap": True},
                    ],
                },
            },
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1ef\U0001f1f5 \u6771\u4eac", "text": "\u4f4f\u5bbf \u6771\u4eac"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1f0\U0001f1f7 \u9996\u723e", "text": "\u4f4f\u5bbf \u9996\u723e"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1f9\U0001f1ed \u66fc\u8c37", "text": "\u4f4f\u5bbf \u66fc\u8c37"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1ef\U0001f1f5 \u5927\u962a", "text": "\u4f4f\u5bbf \u5927\u962a"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1f8\U0001f1ec \u65b0\u52a0\u5761", "text": "\u4f4f\u5bbf \u65b0\u52a0\u5761"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1ed\U0001f1f0 \u9999\u6e2f", "text": "\u4f4f\u5bbf \u9999\u6e2f"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1fb\U0001f1f3 \u8d8a\u5357", "text": "\u4f4f\u5bbf \u8d8a\u5357"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f1ef\U0001f1f5 \u6c96\u7e04", "text": "\u4f4f\u5bbf \u6c96\u7e04"}},
                ],
            },
        }]

    dest_code = parse_destination(clean)
    if not dest_code:
        return [{"type": "text", "text":
            f"\u627e\u4e0d\u5230\u300c{clean}\u300d\u7684\u4f4f\u5bbf\u8cc7\u8a0a\n\n"
            f"\u8acb\u8f38\u5165\u57ce\u5e02\u540d\u7a31\uff0c\u4f8b\u5982\uff1a\u300c\u4f4f\u5bbf \u6771\u4eac\u300d"}]

    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    flag = CITY_FLAG.get(dest_code, "\U0001f3e8")
    city_kw = AGODA_CITY_KEYWORDS.get(dest_code, city_name)
    depart, ret = parse_date_range(clean)

    agoda = agoda_url(city_kw, depart, ret)
    booking = booking_url(city_kw)
    trip_com = f"https://www.trip.com/hotels/?city={city_kw}&locale=zh-TW&curr=TWD"
    google_hotels = f"https://www.google.com/travel/hotels/{city_kw}?hl=zh-TW&curr=TWD"

    date_text = ""
    if depart:
        d = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
        date_text = f"\U0001f4c5 {d}"
        if ret:
            r = ret[5:].replace("-", "/") if len(ret) >= 10 else ret
            date_text += f" ~ {r}"

    body_contents = [
        {"type": "text", "text": "\u591a\u5e73\u53f0\u6bd4\u50f9\uff0c\u627e\u5230\u6700\u5212\u7b97\u7684\u4f4f\u5bbf\uff01",
         "size": "sm", "color": "#666666", "wrap": True},
    ]
    if date_text:
        body_contents.append({"type": "text", "text": date_text, "size": "sm", "color": "#888888", "margin": "sm"})
    body_contents.append({"type": "separator", "margin": "md"})
    body_contents.append({
        "type": "text", "text":
            "\U0001f4a1 \u5c0f\u6280\u5de7\uff1a\n"
            "\u2022 Agoda \u5e38\u6709\u4eca\u65e5\u7279\u50f9\n"
            "\u2022 Booking.com \u591a\u53ef\u514d\u8cbb\u53d6\u6d88\n"
            "\u2022 Trip.com \u504f\u5411\u4e9e\u6d32\u98ef\u5e97\n"
            "\u2022 Google \u53ef\u7dbc\u89bd\u6240\u6709\u5e73\u53f0\u50f9\u683c",
        "size": "xs", "color": "#999999", "wrap": True, "margin": "md",
    })

    return [{
        "type": "flex",
        "altText": f"{city_name} \u4f4f\u5bbf\u63a8\u85a6",
        "contents": {
            "type": "bubble", "size": "mega",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E8C", "paddingAll": "15px",
                "contents": [
                    {"type": "text", "text": f"{flag} {city_name} \u4f4f\u5bbf\u63a8\u85a6",
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "15px",
                "contents": body_contents,
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "10px",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#E91E8C", "height": "sm",
                     "action": {"type": "uri", "label": "\U0001f3e8 Agoda", "uri": agoda}},
                    {"type": "button", "style": "primary", "color": "#003580", "height": "sm",
                     "action": {"type": "uri", "label": "\U0001f3e8 Booking.com", "uri": booking}},
                    {"type": "button", "style": "primary", "color": "#2577E3", "height": "sm",
                     "action": {"type": "uri", "label": "\U0001f3e8 Trip.com", "uri": trip_com}},
                    {"type": "button", "style": "primary", "color": "#4285F4", "height": "sm",
                     "action": {"type": "uri", "label": "\U0001f310 Google Hotels", "uri": google_hotels}},
                ],
            },
        },
    }]
