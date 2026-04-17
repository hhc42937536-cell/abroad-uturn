"""URL 產生器：Skyscanner, Google Flights, Agoda, Booking"""

import urllib.parse

# ── Google Travel Explore：台灣出發 → 全球（已驗證可用的 tfs protobuf）──
# 來源：TPE/KHH → 全球，來回，Google Travel Explore 實際 URL 截取
_EXPLORE_TFS_TW = (
    "CBwQAxocagwIAhIIL20vMDRibnhyDAgEEggvbS8wMmo3MRocagwIBBIIL20vMDJqNzFy"
    "DAgCEggvbS8wNGJueEABSAFwAoIBCwj___________8BmAEBsgEEGAEgAQ"
)


def skyscanner_url(origin: str, dest: str, depart: str, ret: str = "") -> str:
    dep_d = depart.replace("-", "")[:8] if len(depart) >= 8 else ""
    base = f"https://www.skyscanner.com.tw/transport/flights/{origin.upper()}/{dest.upper()}"
    if dep_d:
        base += f"/{dep_d}"
        if ret:
            base += f"/{ret.replace('-', '')[:8]}"
    base += "/?adultsv2=1&cabinclass=economy&currency=TWD&locale=zh-TW"
    return base


def google_flights_url(origin: str, dest: str, depart: str, ret: str = "") -> str:
    """Google Flights 特定航線連結（城市名搜尋，相容性最佳）"""
    try:
        from bot.constants.cities import IATA_TO_NAME
        dest_city = IATA_TO_NAME.get(dest, dest)
    except Exception:
        dest_city = dest
    q = f"flights from {origin} to {dest_city}"
    if depart:
        q += f" on {depart}"
    if ret:
        q += f" return {ret}"
    params = urllib.parse.urlencode({"q": q, "hl": "zh-TW", "curr": "TWD"})
    return f"https://www.google.com/travel/flights?{params}"


def google_explore_url(origin: str = "TPE") -> str:
    """Google Travel Explore 全球探索（含正確 tfs，可直接開啟價格地圖）"""
    return f"https://www.google.com/travel/explore?tfs={_EXPLORE_TFS_TW}&tfu=GgA&hl=zh-TW"


def agoda_url(city_keyword: str, checkin: str = "", checkout: str = "") -> str:
    params = {"q": city_keyword, "currency": "TWD", "language": "zh-tw"}
    if checkin:
        params["checkIn"] = checkin
        params["checkOut"] = checkout if checkout else checkin
    return f"https://www.agoda.com/zh-tw/search?{urllib.parse.urlencode(params)}"


def booking_url(city_keyword: str) -> str:
    return f"https://www.booking.com/searchresults.zh-tw.html?ss={urllib.parse.quote(city_keyword)}"
