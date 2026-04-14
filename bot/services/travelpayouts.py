"""Travelpayouts 機票 API + Mock 資料"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.parse

from bot.config import TRAVELPAYOUTS_TOKEN

_tp_cache = {}


def _tp_api(endpoint: str, params: dict) -> dict | list | None:
    """呼叫 Travelpayouts API，有 5 分鐘 in-memory 快取"""
    cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
    now = time.time()

    cached = _tp_cache.get(cache_key)
    if cached and now - cached["ts"] < 300:
        return cached["data"]

    if TRAVELPAYOUTS_TOKEN:
        params["token"] = TRAVELPAYOUTS_TOKEN

    params.setdefault("currency", "twd")
    qs = urllib.parse.urlencode(params)
    url = f"https://api.travelpayouts.com/aviasales/v3/{endpoint}?{qs}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AbroadUturn/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            data = result.get("data") if isinstance(result, dict) else result
            _tp_cache[cache_key] = {"data": data, "ts": now}
            return data
    except Exception as e:
        print(f"[tp_api] {endpoint} ERROR: {e}")
        return None


def search_cheapest_by_month(origin: str, month: str) -> list | None:
    return _tp_api("prices_for_dates", {
        "origin": origin,
        "departure_at": month,
        "sorting": "price",
        "direct": "false",
        "limit": 30,
        "page": 1,
        "one_way": "false",
    })


def search_flights(origin: str, destination: str, depart: str, ret: str = "") -> list | None:
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": depart,
        "sorting": "price",
        "direct": "false",
        "limit": 30,
    }
    if ret:
        params["return_at"] = ret
    return _tp_api("prices_for_dates", params)


def search_cheapest_any(origin: str, **kwargs) -> list | None:
    params = {
        "origin": origin,
        "sorting": "price",
        "limit": 50,
        "one_way": "false",
        **kwargs,
    }
    return _tp_api("prices_for_dates", params)


# ─── Mock 資料 ──────────────────────────────────────

def mock_explore_data(month: str, origin: str = "TPE") -> list:
    return [
        {"origin": origin, "destination": "NRT", "price": 4280,
         "airline": "MM", "departure_at": f"{month}-15", "return_at": f"{month}-20",
         "transfers": 0, "duration": 210, "duration_to": 210, "duration_back": 225},
        {"origin": origin, "destination": "ICN", "price": 3650,
         "airline": "7C", "departure_at": f"{month}-10", "return_at": f"{month}-14",
         "transfers": 0, "duration": 165, "duration_to": 165, "duration_back": 170},
        {"origin": origin, "destination": "BKK", "price": 5120,
         "airline": "TG", "departure_at": f"{month}-08", "return_at": f"{month}-13",
         "transfers": 0, "duration": 225, "duration_to": 225, "duration_back": 220},
        {"origin": origin, "destination": "DPS", "price": 6800,
         "airline": "CI", "departure_at": f"{month}-12", "return_at": f"{month}-17",
         "transfers": 1, "duration": 420, "duration_to": 420, "duration_back": 430},
        {"origin": origin, "destination": "SIN", "price": 5580,
         "airline": "TR", "departure_at": f"{month}-20", "return_at": f"{month}-25",
         "transfers": 0, "duration": 270, "duration_to": 270, "duration_back": 265},
        {"origin": origin, "destination": "OSA", "price": 4950,
         "airline": "MM", "departure_at": f"{month}-05", "return_at": f"{month}-10",
         "transfers": 0, "duration": 195, "duration_to": 195, "duration_back": 210},
        {"origin": origin, "destination": "HKG", "price": 3280,
         "airline": "CX", "departure_at": f"{month}-18", "return_at": f"{month}-21",
         "transfers": 0, "duration": 105, "duration_to": 105, "duration_back": 115},
        {"origin": origin, "destination": "SGN", "price": 4150,
         "airline": "VJ", "departure_at": f"{month}-22", "return_at": f"{month}-27",
         "transfers": 0, "duration": 195, "duration_to": 195, "duration_back": 200},
    ]


def mock_flight_data(origin: str, dest: str, depart: str, ret: str) -> list:
    import random
    base = random.randint(3000, 8000)
    airlines = [
        ("CI", "中華航空", 0), ("BR", "長榮航空", 200),
        ("MM", "樂桃航空", -800), ("TR", "酷航", -600),
        ("7C", "濟州航空", -500), ("TG", "泰航", 300),
    ]
    results = []
    for code, name, delta in airlines[:4]:
        price = max(2000, base + delta + random.randint(-200, 200))
        transfers = 0 if random.random() > 0.3 else 1
        results.append({
            "origin": origin, "destination": dest, "price": price,
            "airline": code, "departure_at": depart, "return_at": ret or "",
            "transfers": transfers, "duration": random.randint(120, 480),
            "duration_to": random.randint(120, 300),
            "duration_back": random.randint(120, 300),
        })
    results.sort(key=lambda x: x["price"])
    return results
