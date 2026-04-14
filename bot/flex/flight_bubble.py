"""機票 Flex Bubble 卡片建構"""

from bot.constants.cities import IATA_TO_NAME, CITY_FLAG
from bot.constants.airlines import airline_name
from bot.utils.date_parser import duration_str
from bot.utils.url_builder import skyscanner_url, google_flights_url


def flight_bubble(flight: dict, rank: int = 0, show_track_btn: bool = True) -> dict:
    """建立單張航班 Flex Bubble"""
    dest = flight.get("destination", "")
    city_name = IATA_TO_NAME.get(dest, dest)
    flag = CITY_FLAG.get(dest, "\u2708\ufe0f")
    price = flight.get("price", 0)
    airline = airline_name(flight.get("airline", ""))
    depart = flight.get("departure_at", "")
    ret = flight.get("return_at", "")
    transfers = flight.get("transfers", 0)
    dur_to = flight.get("duration_to", flight.get("duration", 0))

    transfer_text = "\u2708\ufe0f \u76f4\u98db" if transfers == 0 else f"\U0001f504 \u8f49\u6a5f{transfers}\u6b21"
    duration_text = duration_str(dur_to)

    header_colors = ["#FF6B35", "#2196F3", "#4CAF50", "#9C27B0", "#FF9800"]
    header_bg = header_colors[rank % len(header_colors)]

    rank_labels = ["\U0001f947 \u53c3\u8003\u6700\u4f4e", "\U0001f948 \u7b2c\u4e8c\u4f4e", "\U0001f949 \u7b2c\u4e09", "", ""]
    rank_text = rank_labels[rank] if rank < len(rank_labels) else ""

    header_contents = []
    if rank_text:
        header_contents.append({
            "type": "text", "text": rank_text,
            "color": "#FFFFFF", "size": "xs", "weight": "bold",
        })
    header_contents.append({
        "type": "text", "text": f"{flag} {city_name} ({dest})",
        "color": "#FFFFFF", "weight": "bold", "size": "lg",
    })

    date_display = ""
    if depart:
        d = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
        date_display = f"\U0001f4c5 {d}"
        if ret:
            r = ret[5:].replace("-", "/") if len(ret) >= 10 else ret
            date_display += f" \u2192 {r}"

    body_contents = [
        {
            "type": "text",
            "text": f"NT$ {price:,} \u542b\u7a05\u8d77",
            "size": "xl", "weight": "bold", "color": "#E53935",
        },
        {
            "type": "text",
            "text": "\u6b77\u53f2\u53c3\u8003\u4f4e\u50f9\u30fb\u5be6\u969b\u4ee5\u8a02\u7968\u7db2\u7ad9\u70ba\u6e96",
            "size": "xxs", "color": "#999999", "margin": "xs",
        },
        {"type": "separator", "margin": "md"},
    ]
    if date_display:
        body_contents.append({
            "type": "text", "text": date_display,
            "size": "sm", "color": "#555555", "margin": "md",
        })

    gate = flight.get("gate", "")
    airline_gate = f"\u2708\ufe0f {airline}"
    if gate:
        airline_gate += f" \u00b7 {gate}"
    airline_gate += f" \u00b7 {transfer_text}"

    body_contents.append({
        "type": "text", "text": airline_gate,
        "size": "sm", "color": "#555555", "margin": "sm", "wrap": True,
    })
    if duration_text:
        body_contents.append({
            "type": "text", "text": f"\u23f1\ufe0f {duration_text}",
            "size": "sm", "color": "#888888", "margin": "sm",
        })

    origin = flight.get("origin", "TPE")
    link = flight.get("link", "")
    booking_url = skyscanner_url(origin, dest, depart, ret)
    google_url = google_flights_url(origin, dest, depart, ret)

    footer_contents = [
        {
            "type": "button", "style": "primary", "color": "#00B0F0",
            "height": "sm",
            "action": {"type": "uri", "label": "\U0001f50d Skyscanner \u67e5\u7968", "uri": booking_url},
        },
        {
            "type": "button", "style": "primary", "color": "#4285F4",
            "height": "sm",
            "action": {"type": "uri", "label": "\U0001f310 Google Flights \u6bd4\u50f9", "uri": google_url},
        },
    ]
    if show_track_btn:
        track_data = f"\u8ffd\u8e64|{origin}|{dest}|{depart}|{ret}"
        footer_contents.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": "\U0001f4e2 \u8ffd\u8e64\u964d\u50f9\u901a\u77e5", "text": track_data},
        })

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_bg,
            "paddingAll": "15px",
            "contents": header_contents,
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "15px",
            "contents": body_contents,
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "10px",
            "contents": footer_contents,
        },
    }
