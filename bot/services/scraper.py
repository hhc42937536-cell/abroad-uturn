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


def scrape_idol_events(artist_name: str, country: str = "", search_name: str = "",
                       is_actor: bool = False) -> list:
    """
    爬蟲搜尋藝人/演員活動資訊
    search_name: 英文搜尋名（優先用於外部平台搜尋）
    is_actor: True 時走演員專用來源（Interpark / Melon Ticket）
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
    query = search_name if search_name else artist_name

    if is_actor:
        # 演員：搜尋 Interpark / Melon Ticket 粉絲見面會
        events.extend(_scrape_interpark_actor(query))
        if not events:
            events.extend(_scrape_songkick(query))
    else:
        # 歌手/偶像：Kpopmap（KR）→ Bandsintown → Songkick
        if country == "KR":
            try:
                from bot.services.trending import scrape_kpopmap_events
                kpop_events = scrape_kpopmap_events()
                name_lower = query.lower()
                matched = [e for e in kpop_events
                           if name_lower in e.get("title", "").lower()
                           or name_lower in e.get("artist", "").lower()]
                events.extend(matched)
            except Exception as e:
                print(f"[scraper] Kpopmap error: {e}")

        if not events:
            events.extend(_scrape_bandsintown(query))
        if not events:
            events.extend(_scrape_songkick(query))

    if events:
        redis_set(cache_key, json.dumps(events, ensure_ascii=False), ttl=21600)

    return events[:10]


def _scrape_interpark_actor(search_name: str) -> list:
    """搜尋 Interpark 韓國演員粉絲見面會"""
    events = []
    try:
        query = urllib.parse.quote(search_name)
        url = f"https://ticket.interpark.com/webzine/paper/TPNoticeList_Calendar.asp?SearchWord={query}"
        html = _fetch_url(url, timeout=12)
        if not html:
            return []

        # 解析活動標題與日期
        title_matches = re.findall(
            r'<td[^>]*class="[^"]*subject[^"]*"[^>]*>.*?<a[^>]*>(.*?)</a>',
            html, re.DOTALL | re.IGNORECASE
        )
        date_matches = re.findall(
            r'(\d{4}[.\-]\d{2}[.\-]\d{2})',
            html
        )
        for i, title in enumerate(title_matches[:8]):
            clean_title = re.sub(r"<[^>]+>", "", title).strip()
            if not clean_title or len(clean_title) < 3:
                continue
            if search_name.lower() not in clean_title.lower():
                continue
            date = date_matches[i].replace(".", "-") if i < len(date_matches) else ""
            events.append({
                "title": clean_title,
                "date": date,
                "venue": "",
                "city": "首爾",
                "url": f"https://ticket.interpark.com/webzine/paper/TPNoticeList_Calendar.asp?SearchWord={urllib.parse.quote(search_name)}",
            })
    except Exception as e:
        print(f"[scraper] Interpark error: {e}")
    return events


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
