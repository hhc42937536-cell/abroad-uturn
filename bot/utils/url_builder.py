"""URL 產生器：Skyscanner, Google Flights, Agoda, Booking"""

import urllib.parse

# ── Google Travel Explore：台灣出發 → 全球（已驗證可用的 tfs protobuf）──
# 來源：TPE/KHH → 全球，來回，Google Travel Explore 實際 URL 截取
_EXPLORE_TFS_TW = (
    "CBwQAxocagwIAhIIL20vMDRibnhyDAgEEggvbS8wMmo3MRocagwIBBIIL20vMDJqNzFy"
    "DAgCEggvbS8wNGJueEABSAFwAoIBCwj___________8BmAEBsgEEGAEgAQ"
)


def _iso_to_ymd(date_str: str) -> str:
    """從 ISO 8601 字串（含時區）取 YYYY-MM-DD"""
    return date_str[:10] if date_str else ""


def skyscanner_url(origin: str, dest: str, depart: str, ret: str = "") -> str:
    dep_d = _iso_to_ymd(depart).replace("-", "")
    base = f"https://www.skyscanner.com.tw/transport/flights/{origin.upper()}/{dest.upper()}"
    if dep_d:
        base += f"/{dep_d}"
        ret_d = _iso_to_ymd(ret).replace("-", "")
        if ret_d:
            base += f"/{ret_d}"
    base += "/?adultsv2=1&cabinclass=economy&currency=TWD&locale=zh-TW"
    return base


def google_flights_url(origin: str, dest: str, depart: str, ret: str = "") -> str:
    """Google Flights 直接航線連結（IATA code，避免中文城市名跑掉）"""
    dep_d = _iso_to_ymd(depart)
    ret_d = _iso_to_ymd(ret)
    flt = f"{origin.upper()}.{dest.upper()}.{dep_d}"
    if ret_d:
        flt += f"*{dest.upper()}.{origin.upper()}.{ret_d}"
    return f"https://www.google.com/flights#flt={flt};c:TWD;e:1;sd:1;t:f"


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
