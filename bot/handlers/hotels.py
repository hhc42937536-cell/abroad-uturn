"""格5：住宿推薦獨立入口"""

from bot.constants.cities import IATA_TO_NAME, AGODA_CITY_KEYWORDS, CITY_FLAG
from bot.utils.date_parser import parse_destination, parse_date_range
from bot.utils.url_builder import agoda_url, booking_url

# 各城市住宿估算資訊（每晚 TWD，評分，推薦住宿區域）
_HOTEL_ESTIMATES = {
    "NRT": {"price": "1,200~3,500", "rating": "8.5", "area": "新宿・淺草・池袋"},
    "TYO": {"price": "1,200~3,500", "rating": "8.5", "area": "新宿・淺草・池袋"},
    "HND": {"price": "1,200~3,500", "rating": "8.5", "area": "新宿・淺草・池袋"},
    "KIX": {"price": "900~2,800",  "rating": "8.3", "area": "難波・心齋橋・梅田"},
    "OSA": {"price": "900~2,800",  "rating": "8.3", "area": "難波・心齋橋・梅田"},
    "ICN": {"price": "800~2,500",  "rating": "8.4", "area": "弘大・明洞・江南"},
    "SEL": {"price": "800~2,500",  "rating": "8.4", "area": "弘大・明洞・江南"},
    "BKK": {"price": "500~2,000",  "rating": "8.2", "area": "暹羅・素坤逸・考山路"},
    "DMK": {"price": "500~2,000",  "rating": "8.2", "area": "暹羅・素坤逸・考山路"},
    "SIN": {"price": "1,500~4,500","rating": "8.6", "area": "烏節路・牛車水・克拉碼頭"},
    "HKG": {"price": "1,800~5,000","rating": "8.4", "area": "尖沙咀・旺角・銅鑼灣"},
    "SGN": {"price": "400~1,500",  "rating": "8.1", "area": "第一郡・濱城市場周邊"},
    "HAN": {"price": "350~1,200",  "rating": "8.0", "area": "還劍湖・老城區・西湖"},
    "DPS": {"price": "600~2,500",  "rating": "8.5", "area": "庫塔・烏布・水明漾"},
    "KUL": {"price": "500~2,000",  "rating": "8.2", "area": "武吉免登・KLCC・茨廠街"},
    "OKA": {"price": "800~2,200",  "rating": "8.3", "area": "那霸・國際通・美浜"},
    "FUK": {"price": "900~2,500",  "rating": "8.3", "area": "博多・天神・中洲"},
    "PUS": {"price": "700~2,000",  "rating": "8.2", "area": "海雲台・西面・南浦洞"},
}

_DEFAULT_ESTIMATE = {"price": "500~3,000", "rating": "8.2", "area": "市中心・交通便利區"}


def _get_estimate(dest_code: str) -> dict:
    return _HOTEL_ESTIMATES.get(dest_code, _DEFAULT_ESTIMATE)


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
    est = _get_estimate(dest_code)

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
        # 估算資訊卡
        {
            "type": "box", "layout": "horizontal",
            "backgroundColor": "#FFF0F5", "paddingAll": "10px",
            "cornerRadius": "8px", "margin": "sm",
            "contents": [
                {
                    "type": "box", "layout": "vertical", "flex": 1,
                    "contents": [
                        {"type": "text", "text": "\U0001f4b0 \u5c0f\u8a08\u4f30\u7b97",
                         "size": "xxs", "color": "#C2185B", "weight": "bold"},
                        {"type": "text", "text": f"NT$ {est['price']}/\u6674",
                         "size": "sm", "color": "#333333", "weight": "bold"},
                    ],
                },
                {
                    "type": "box", "layout": "vertical", "flex": 1,
                    "contents": [
                        {"type": "text", "text": "\u2b50 \u5e73\u5747\u8a55\u5206",
                         "size": "xxs", "color": "#C2185B", "weight": "bold"},
                        {"type": "text", "text": est["rating"],
                         "size": "sm", "color": "#333333", "weight": "bold"},
                    ],
                },
                {
                    "type": "box", "layout": "vertical", "flex": 2,
                    "contents": [
                        {"type": "text", "text": "\U0001f4cd \u63a8\u85a6\u4f4f\u5bbf\u5340",
                         "size": "xxs", "color": "#C2185B", "weight": "bold"},
                        {"type": "text", "text": est["area"],
                         "size": "xs", "color": "#555555", "wrap": True},
                    ],
                },
            ],
        },
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
