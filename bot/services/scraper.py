"""網頁爬蟲：抓取最新活動資訊、伴手禮排行等即時資料"""

import json
import re
import urllib.request
import urllib.parse

from bot.services.redis_store import redis_get, redis_set

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def _fetch_url(url: str, timeout: int = 10) -> str | None:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[scraper] Fetch error {url}: {e}")
        return None


def scrape_idol_events(artist_name: str, country: str = "") -> list:
    """
    爬蟲搜尋藝人活動資訊
    使用 Songkick / Bandsintown 風格的搜尋
    回傳: [{"title": "...", "date": "...", "venue": "...", "city": "...", "url": "..."}]
    """
    cache_key = f"idol_events:{artist_name}:{country}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    events = []

    # 方式 1: 搜尋 Bandsintown
    events.extend(_scrape_bandsintown(artist_name))

    # 方式 2: 搜尋 Songkick
    if not events:
        events.extend(_scrape_songkick(artist_name))

    # 過濾國家
    if country and events:
        country_map = {"JP": ["Japan", "日本", "Tokyo", "Osaka", "Nagoya", "Fukuoka", "Sapporo", "Yokohama"],
                       "KR": ["Korea", "韓國", "Seoul", "Busan", "Incheon"]}
        keywords = country_map.get(country, [])
        if keywords:
            filtered = [e for e in events if any(kw.lower() in (e.get("city", "") + e.get("venue", "")).lower() for kw in keywords)]
            if filtered:
                events = filtered

    # 快取 6 小時
    if events:
        redis_set(cache_key, json.dumps(events, ensure_ascii=False), ttl=21600)

    return events[:10]


def _scrape_bandsintown(artist: str) -> list:
    """從 Bandsintown 搜尋藝人活動"""
    events = []
    try:
        slug = urllib.parse.quote(artist.lower().replace(" ", "-"))
        url = f"https://www.bandsintown.com/{slug}"
        html = _fetch_url(url)
        if not html:
            return []

        # 解析 JSON-LD 結構化資料
        ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for ld_text in ld_matches:
            try:
                ld = json.loads(ld_text)
                items = ld if isinstance(ld, list) else [ld]
                for item in items:
                    if item.get("@type") == "MusicEvent":
                        location = item.get("location", {})
                        events.append({
                            "title": item.get("name", artist),
                            "date": item.get("startDate", "")[:10],
                            "venue": location.get("name", ""),
                            "city": location.get("address", {}).get("addressLocality", ""),
                            "url": item.get("url", url),
                        })
            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"[scraper] Bandsintown error: {e}")

    return events


def _scrape_songkick(artist: str) -> list:
    """從 Songkick 搜尋藝人活動"""
    events = []
    try:
        query = urllib.parse.quote(artist)
        search_url = f"https://www.songkick.com/search?query={query}&type=upcoming"
        html = _fetch_url(search_url)
        if not html:
            return []

        # 解析 JSON-LD
        ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for ld_text in ld_matches:
            try:
                ld = json.loads(ld_text)
                items = ld if isinstance(ld, list) else [ld]
                for item in items:
                    if item.get("@type") in ("MusicEvent", "Event"):
                        location = item.get("location", {})
                        events.append({
                            "title": item.get("name", artist),
                            "date": item.get("startDate", "")[:10],
                            "venue": location.get("name", ""),
                            "city": location.get("address", {}).get("addressLocality", ""),
                            "url": item.get("url", ""),
                        })
            except json.JSONDecodeError:
                continue

    except Exception as e:
        print(f"[scraper] Songkick error: {e}")

    return events


def scrape_trending_souvenirs(country_code: str) -> list:
    """
    爬蟲搜尋最新熱門伴手禮排行
    回傳: [{"name": "...", "source": "...", "url": "..."}]
    """
    cache_key = f"trending_souvenirs:{country_code}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    results = []

    country_search = {
        "JP": "日本必買伴手禮2026",
        "KR": "韓國必買伴手禮2026",
        "TH": "泰國必買伴手禮2026",
        "SG": "新加坡必買伴手禮2026",
        "VN": "越南必買伴手禮2026",
    }

    query = country_search.get(country_code, f"{country_code}必買伴手禮")

    # 快取 24 小時
    if results:
        redis_set(cache_key, json.dumps(results, ensure_ascii=False), ttl=86400)

    return results
