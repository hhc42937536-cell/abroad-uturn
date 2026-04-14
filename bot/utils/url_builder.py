"""URL 產生器：Skyscanner, Google Flights, Agoda, Booking"""

import urllib.parse


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
    q = f"flights from {origin} to {dest}"
    if depart:
        q += f" {depart}"
    if ret:
        q += f" to {ret}"
    params = urllib.parse.urlencode({"q": q, "hl": "zh-TW", "curr": "TWD"})
    return f"https://www.google.com/travel/flights?{params}"


def google_explore_url(origin: str = "TPE") -> str:
    return f"https://www.google.com/travel/explore?hl=zh-TW&curr=TWD"


def agoda_url(city_keyword: str, checkin: str = "", checkout: str = "") -> str:
    params = {"q": city_keyword, "currency": "TWD", "language": "zh-tw"}
    if checkin:
        params["checkIn"] = checkin
        params["checkOut"] = checkout if checkout else checkin
    return f"https://www.agoda.com/zh-tw/search?{urllib.parse.urlencode(params)}"


def booking_url(city_keyword: str) -> str:
    return f"https://www.booking.com/searchresults.zh-tw.html?ss={urllib.parse.quote(city_keyword)}"
