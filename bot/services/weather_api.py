"""Open-Meteo 天氣 API（免費、免 key）

支援兩種模式：
- 預報模式：16 天內用 /v1/forecast（精確）
- 歷史模式：超過 16 天用 /v1/climate 取同月歷史平均（估算）
"""

import json
import urllib.request
import urllib.parse
import datetime

from bot.constants.cities import CITY_COORDINATES
from bot.services.redis_store import redis_get, redis_set


def _describe(avg_h: float, rain_pct: int) -> str:
    if avg_h >= 30:
        desc = "炎熱，注意防曬補水"
    elif avg_h >= 25:
        desc = "溫暖舒適，適合觀光"
    elif avg_h >= 18:
        desc = "涼爽，建議帶薄外套"
    elif avg_h >= 10:
        desc = "偏冷，需準備保暖衣物"
    else:
        desc = "寒冷，需準備厚外套"

    if rain_pct >= 60:
        desc += "，多雨需帶雨具"
    elif rain_pct >= 40:
        desc += "，可能有雨建議帶傘"
    return desc


def _fetch_json(url: str, timeout: int = 10) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AbroadUturn/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[weather] Fetch error: {e}")
        return None


def get_weather(iata_code: str, start_date: str, end_date: str) -> dict | None:
    """
    取得目的地天氣資料
    - 16 天內：用即時預報
    - 超過 16 天：用歷史同月平均
    """
    coords = CITY_COORDINATES.get(iata_code)
    if not coords:
        return None

    cache_key = f"weather:{iata_code}:{start_date}:{end_date}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    lat, lon = coords

    # 正規化日期
    if not start_date:
        return None
    if len(start_date) < 10:
        start_date = f"{start_date}-15"  # YYYY-MM → YYYY-MM-15
    if not end_date or len(end_date) < 10:
        end_date = start_date

    try:
        start_d = datetime.date.fromisoformat(start_date[:10])
        end_d = datetime.date.fromisoformat(end_date[:10])
    except ValueError:
        return None

    today = datetime.date.today()
    days_ahead = (start_d - today).days

    result = None

    # 預報模式（未來 16 天內）
    if 0 <= days_ahead <= 14:
        end_for_forecast = min(end_d, today + datetime.timedelta(days=15))
        params = {
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "start_date": start_d.isoformat(),
            "end_date": end_for_forecast.isoformat(),
            "timezone": "auto",
        }
        url = f"https://api.open-meteo.com/v1/forecast?{urllib.parse.urlencode(params)}"
        data = _fetch_json(url)
        if data and data.get("daily"):
            daily = data["daily"]
            highs = daily.get("temperature_2m_max") or []
            lows = daily.get("temperature_2m_min") or []
            rains = daily.get("precipitation_probability_max") or []
            if highs:
                result = {
                    "avg_high": round(sum(highs) / len(highs), 1),
                    "avg_low": round(sum(lows) / len(lows), 1),
                    "rain_chance": round(sum(rains) / len(rains)) if rains else 0,
                    "mode": "forecast",
                }

    # 歷史平均模式（未來超過 16 天或已過去）
    if result is None:
        month = start_d.month
        # 用近 3 年同月歷史平均
        hist_year = today.year - 1
        hist_start = datetime.date(hist_year, month, 1)
        # 該月最後一天
        if month == 12:
            hist_end = datetime.date(hist_year, 12, 31)
        else:
            hist_end = datetime.date(hist_year, month + 1, 1) - datetime.timedelta(days=1)

        params = {
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "start_date": hist_start.isoformat(),
            "end_date": hist_end.isoformat(),
            "timezone": "auto",
        }
        url = f"https://archive-api.open-meteo.com/v1/archive?{urllib.parse.urlencode(params)}"
        data = _fetch_json(url)
        if data and data.get("daily"):
            daily = data["daily"]
            highs = [x for x in (daily.get("temperature_2m_max") or []) if x is not None]
            lows = [x for x in (daily.get("temperature_2m_min") or []) if x is not None]
            precips = [x for x in (daily.get("precipitation_sum") or []) if x is not None]
            if highs:
                # 降雨天數比例當作降雨機率估算
                rainy_days = sum(1 for p in precips if p > 1.0)
                rain_pct = round(rainy_days / len(precips) * 100) if precips else 0
                result = {
                    "avg_high": round(sum(highs) / len(highs), 1),
                    "avg_low": round(sum(lows) / len(lows), 1),
                    "rain_chance": rain_pct,
                    "mode": "historical",
                }

    if not result:
        return None

    result["description"] = _describe(result["avg_high"], result["rain_chance"])
    if result["mode"] == "historical":
        result["note"] = "歷史同月平均（實際天氣可能有變化）"

    redis_set(cache_key, json.dumps(result, ensure_ascii=False), ttl=21600)
    return result
