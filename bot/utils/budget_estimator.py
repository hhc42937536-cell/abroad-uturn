"""預估旅遊支出計算器

依目的地、天數、人數估算：機票 / 住宿 / 餐飲 / 當地交通 / 景點活動
所有金額以 TWD（新台幣）為單位，為一人份參考中間值。
"""

# ── 各目的地每人每天花費（TWD，不含機票）────────────────
# 格式：{IATA: {"hotel": 每晚住宿, "food": 每天餐飲, "transport": 每天交通, "activity": 每天活動}}
_DAILY_COST = {
    # 日本
    "NRT": {"hotel": 2800, "food": 1400, "transport": 900, "activity": 1200},
    "HND": {"hotel": 3000, "food": 1500, "transport": 900, "activity": 1200},
    "TYO": {"hotel": 2800, "food": 1400, "transport": 900, "activity": 1200},
    "OSA": {"hotel": 2400, "food": 1200, "transport": 700, "activity": 1000},
    "KIX": {"hotel": 2400, "food": 1200, "transport": 700, "activity": 1000},
    "FUK": {"hotel": 2000, "food": 1000, "transport": 600, "activity": 800},
    "OKA": {"hotel": 2200, "food": 1000, "transport": 500, "activity": 900},
    "CTS": {"hotel": 2200, "food": 1100, "transport": 700, "activity": 900},
    "NGO": {"hotel": 2000, "food": 1000, "transport": 700, "activity": 800},
    # 韓國
    "ICN": {"hotel": 2000, "food": 900,  "transport": 500, "activity": 800},
    "SEL": {"hotel": 2000, "food": 900,  "transport": 500, "activity": 800},
    "PUS": {"hotel": 1600, "food": 800,  "transport": 400, "activity": 700},
    "CJU": {"hotel": 1800, "food": 800,  "transport": 500, "activity": 700},
    # 東南亞
    "BKK": {"hotel": 1200, "food": 600,  "transport": 300, "activity": 600},
    "CNX": {"hotel": 900,  "food": 500,  "transport": 250, "activity": 500},
    "HKT": {"hotel": 1500, "food": 700,  "transport": 300, "activity": 700},
    "SIN": {"hotel": 3500, "food": 1000, "transport": 400, "activity": 900},
    "KUL": {"hotel": 1000, "food": 500,  "transport": 200, "activity": 500},
    "SGN": {"hotel": 900,  "food": 450,  "transport": 200, "activity": 500},
    "HAN": {"hotel": 800,  "food": 400,  "transport": 180, "activity": 400},
    "DPS": {"hotel": 1500, "food": 700,  "transport": 400, "activity": 800},
    "MNL": {"hotel": 1000, "food": 500,  "transport": 300, "activity": 500},
    "CEB": {"hotel": 1100, "food": 500,  "transport": 300, "activity": 600},
    # 港澳
    "HKG": {"hotel": 2500, "food": 1000, "transport": 300, "activity": 800},
    "MFM": {"hotel": 2000, "food": 800,  "transport": 200, "activity": 700},
    # 歐洲
    "LON": {"hotel": 6000, "food": 2500, "transport": 1200, "activity": 1500},
    "PAR": {"hotel": 5500, "food": 2200, "transport": 1000, "activity": 1500},
    "ROM": {"hotel": 4500, "food": 1800, "transport": 800,  "activity": 1200},
    "BCN": {"hotel": 4000, "food": 1600, "transport": 700,  "activity": 1000},
    "AMS": {"hotel": 5000, "food": 2000, "transport": 900,  "activity": 1200},
    "FRA": {"hotel": 4500, "food": 1800, "transport": 900,  "activity": 1000},
    "VIE": {"hotel": 4000, "food": 1600, "transport": 800,  "activity": 1000},
    "PRG": {"hotel": 3000, "food": 1200, "transport": 600,  "activity": 800},
    "IST": {"hotel": 2500, "food": 1000, "transport": 500,  "activity": 800},
    # 美洲
    "NYC": {"hotel": 7000, "food": 3000, "transport": 1200, "activity": 1500},
    "LAX": {"hotel": 6000, "food": 2500, "transport": 1500, "activity": 1200},
    "SFO": {"hotel": 6500, "food": 2500, "transport": 1200, "activity": 1200},
    "YVR": {"hotel": 4500, "food": 2000, "transport": 800,  "activity": 1000},
    # 大洋洲
    "SYD": {"hotel": 4500, "food": 2000, "transport": 900,  "activity": 1200},
    "MEL": {"hotel": 4000, "food": 1800, "transport": 800,  "activity": 1000},
    # 其他
    "DXB": {"hotel": 4000, "food": 1500, "transport": 600,  "activity": 1000},
    "ROR": {"hotel": 3000, "food": 1200, "transport": 800,  "activity": 1500},
    "GUM": {"hotel": 2800, "food": 1100, "transport": 600,  "activity": 1000},
}

# 預設值（未知目的地）
_DEFAULT = {"hotel": 2000, "food": 900, "transport": 500, "activity": 800}


def estimate_budget(
    dest: str,
    days: int,
    adults: int,
    flight_price_per_person: int,
) -> dict:
    """
    估算旅遊總花費
    回傳: {
        "flight": 機票總額,
        "hotel": 住宿總額（N晚）,
        "food": 餐飲總額,
        "transport": 當地交通總額,
        "activity": 景點活動總額,
        "total": 總計,
        "nights": 住宿晚數,
        "days": 天數,
        "adults": 人數,
        "per_person": 每人總花費,
        "daily_cost": 每人每天非機票花費,
    }
    """
    cost = _DAILY_COST.get(dest, _DEFAULT)
    nights = max(days - 1, 1)

    flight_total  = flight_price_per_person * adults
    hotel_total   = cost["hotel"]    * nights * adults
    food_total    = cost["food"]     * days   * adults
    transport_total = cost["transport"] * days * adults
    activity_total  = cost["activity"]  * days * adults

    total = flight_total + hotel_total + food_total + transport_total + activity_total
    per_person = total // adults if adults else total
    daily_non_flight = (hotel_total + food_total + transport_total + activity_total) // adults // days if days else 0

    return {
        "flight":    flight_total,
        "hotel":     hotel_total,
        "food":      food_total,
        "transport": transport_total,
        "activity":  activity_total,
        "total":     total,
        "nights":    nights,
        "days":      days,
        "adults":    adults,
        "per_person": per_person,
        "daily_non_flight": daily_non_flight,
    }


def build_budget_bubble(
    dest: str,
    city_name: str,
    days: int,
    adults: int,
    flight_price_per_person: int,
    flag: str = "✈️",
) -> dict:
    """建立預估支出 Flex Bubble"""
    b = estimate_budget(dest, days, adults, flight_price_per_person)
    nights = b["nights"]
    pax = f"{adults}人" if adults > 1 else "1人"
    total_label = f"NT$ {b['total']:,}" if adults == 1 else f"NT$ {b['total']:,}（{pax}）"

    def _row(label: str, value: str, bold: bool = False, color: str = "#333333") -> dict:
        return {
            "type": "box", "layout": "horizontal", "margin": "sm",
            "contents": [
                {"type": "text", "text": label,
                 "size": "sm", "color": "#666666", "flex": 5, "wrap": True},
                {"type": "text", "text": value,
                 "size": "sm", "color": color,
                 "weight": "bold" if bold else "regular",
                 "flex": 5, "align": "end"},
            ],
        }

    rows = [
        _row(f"✈️ 機票（含稅・{pax}）",
             f"NT$ {b['flight']:,}"),
        _row(f"🏨 住宿（{nights}晚・{pax}）",
             f"NT$ {b['hotel']:,}"),
        _row(f"🍜 餐飲（{days}天・{pax}）",
             f"NT$ {b['food']:,}"),
        _row(f"🚇 當地交通（{pax}）",
             f"NT$ {b['transport']:,}"),
        _row(f"🎡 景點活動（{pax}）",
             f"NT$ {b['activity']:,}"),
        {"type": "separator", "margin": "md"},
        _row("💰 預估總計", total_label, bold=True, color="#E53935"),
    ]

    if adults > 1:
        rows.append(_row("📌 每人約",
                         f"NT$ {b['per_person']:,}",
                         bold=False, color="#1565C0"))

    rows.append({
        "type": "text",
        "text": (
            f"💡 每人每天非機票花費約 NT$ {b['daily_non_flight']:,}\n"
            "以上為參考中間值，實際依旅遊方式、住宿等級而異"
        ),
        "size": "xxs", "color": "#AAAAAA",
        "wrap": True, "margin": "md",
    })

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1B5E20", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"{flag} {city_name}",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
                {"type": "text",
                 "text": f"預估旅遊支出 · {days}天{nights}晚 · {pax}",
                 "color": "#A5D6A7", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "xs", "paddingAll": "14px",
            "contents": rows,
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "8px",
            "contents": [
                {"type": "text",
                 "text": "💳 建議準備總額 × 1.2 作為實際預算",
                 "size": "xs", "color": "#4CAF50",
                 "align": "center", "weight": "bold"},
            ],
        },
    }
