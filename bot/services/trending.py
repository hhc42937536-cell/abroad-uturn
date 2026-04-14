"""進階爬蟲：抓取各平台熱門/排行資料

資料來源：
- Kpopmap: K-POP 演唱會/見面會行事曆
- Olive Young: 韓國美妝排行
- Cosme: 日本美妝排行
- Bic Camera: 日本家電排行
- Dcard: 旅遊版熱門貼文

全部用 Redis 快取（12-24 小時）+ 定時 Cron 重新抓取
"""

import json
import re
import urllib.request
import urllib.parse
from html import unescape

from bot.services.redis_store import redis_get, redis_set

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,ja;q=0.8,ko;q=0.7,en;q=0.6",
}


def _fetch(url: str, timeout: int = 15) -> str | None:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[trending] Fetch error {url}: {e}")
        return None


def _clean_text(s: str) -> str:
    """清理 HTML 標籤與特殊字元"""
    s = re.sub(r"<[^>]+>", "", s)
    s = unescape(s)
    return " ".join(s.split()).strip()


# ─── Kpopmap: K-POP 行事曆 ───────────────────────────

def scrape_kpopmap_events(limit: int = 15) -> list:
    """爬 Kpopmap 演唱會/見面會行事曆"""
    cache_key = "trending:kpopmap_events"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    events = []
    html = _fetch("https://www.kpopmap.com/events/calendar/")
    if not html:
        return []

    # JSON-LD 優先
    ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for ld_text in ld_matches:
        try:
            ld = json.loads(ld_text)
            items = ld if isinstance(ld, list) else [ld]
            for item in items:
                if item.get("@type") in ("Event", "MusicEvent"):
                    loc = item.get("location", {})
                    events.append({
                        "title": item.get("name", ""),
                        "date": item.get("startDate", "")[:10],
                        "venue": loc.get("name", "") if isinstance(loc, dict) else "",
                        "city": loc.get("address", {}).get("addressLocality", "") if isinstance(loc, dict) else "",
                        "url": item.get("url", ""),
                    })
        except json.JSONDecodeError:
            continue

    # 備援：解析列表卡片
    if not events:
        # 嘗試抓文章標題
        matches = re.findall(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
        for m in matches[:limit]:
            title_m = re.search(r'<h\d[^>]*>(.*?)</h\d>', m, re.DOTALL)
            link_m = re.search(r'href="([^"]+)"', m)
            if title_m:
                events.append({
                    "title": _clean_text(title_m.group(1)),
                    "date": "",
                    "venue": "",
                    "city": "",
                    "url": link_m.group(1) if link_m else "",
                })

    events = events[:limit]
    if events:
        redis_set(cache_key, json.dumps(events, ensure_ascii=False), ttl=43200)  # 12 小時
    return events


# ─── Olive Young 韓國美妝排行 ────────────────────────

def scrape_oliveyoung_ranking(limit: int = 10) -> list:
    """爬 Olive Young Best Ranking"""
    cache_key = "trending:oliveyoung_ranking"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    items = []
    # Olive Young 全球版（有英文介面）
    url = "https://global.oliveyoung.com/display/category/bestseller"
    html = _fetch(url)
    if not html:
        return []

    # 從 JSON payload 或 li 卡片抓取
    product_matches = re.findall(
        r'<li[^>]*class="[^"]*prd[^"]*"[^>]*>.*?<img[^>]+alt="([^"]+)".*?<span[^>]*class="[^"]*price[^"]*"[^>]*>([^<]+)</span>',
        html, re.DOTALL
    )
    for name, price in product_matches[:limit]:
        items.append({
            "name": _clean_text(name),
            "price": _clean_text(price),
            "source": "Olive Young",
            "url": url,
        })

    if not items:
        # 備援：抓商品名稱 + 排名
        name_matches = re.findall(r'<p[^>]*class="[^"]*tx_name[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
        for i, name in enumerate(name_matches[:limit]):
            items.append({
                "name": _clean_text(name),
                "price": "",
                "rank": i + 1,
                "source": "Olive Young",
                "url": url,
            })

    if items:
        redis_set(cache_key, json.dumps(items, ensure_ascii=False), ttl=86400)  # 24 小時
    return items


# ─── Cosme 日本美妝排行 ──────────────────────────────

def scrape_cosme_ranking(limit: int = 10) -> list:
    """爬 @cosme 日本美妝排行榜"""
    cache_key = "trending:cosme_ranking"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    items = []
    url = "https://www.cosme.net/ranking/"
    html = _fetch(url)
    if not html:
        return []

    # 解析排行榜項目
    rank_matches = re.findall(
        r'<li[^>]*class="[^"]*rank[^"]*"[^>]*>(.*?)</li>',
        html, re.DOTALL
    )
    for i, block in enumerate(rank_matches[:limit]):
        name_m = re.search(r'<p[^>]*class="[^"]*product-name[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
        brand_m = re.search(r'<p[^>]*class="[^"]*brand-name[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
        link_m = re.search(r'href="([^"]+)"', block)

        if name_m:
            items.append({
                "rank": i + 1,
                "name": _clean_text(name_m.group(1)),
                "brand": _clean_text(brand_m.group(1)) if brand_m else "",
                "source": "@cosme",
                "url": f"https://www.cosme.net{link_m.group(1)}" if link_m and link_m.group(1).startswith("/") else (link_m.group(1) if link_m else url),
            })

    if items:
        redis_set(cache_key, json.dumps(items, ensure_ascii=False), ttl=86400)
    return items


# ─── Dcard 旅遊版熱門貼文 ────────────────────────────

def scrape_dcard_travel(category: str = "travel", limit: int = 10) -> list:
    """
    爬 Dcard 看板熱門貼文
    category: "travel"（旅遊）/ "japan_travel" / "korea_travel" / "makeup"
    """
    cache_key = f"trending:dcard:{category}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    items = []
    # Dcard 有公開 API
    url = f"https://www.dcard.tw/service/api/v2/forums/{category}/posts?popular=true&limit={limit}"
    html = _fetch(url)
    if not html:
        # 備援：網頁版
        html = _fetch(f"https://www.dcard.tw/f/{category}")
        if not html:
            return []

    # 嘗試解析 JSON
    try:
        posts = json.loads(html)
        if isinstance(posts, list):
            for p in posts[:limit]:
                items.append({
                    "title": p.get("title", ""),
                    "excerpt": p.get("excerpt", "")[:100],
                    "likes": p.get("likeCount", 0),
                    "comments": p.get("commentCount", 0),
                    "url": f"https://www.dcard.tw/f/{category}/p/{p.get('id', '')}",
                })
    except json.JSONDecodeError:
        # 從 HTML 解析
        title_matches = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        for title in title_matches[:limit]:
            items.append({
                "title": _clean_text(title),
                "url": f"https://www.dcard.tw/f/{category}",
            })

    if items:
        redis_set(cache_key, json.dumps(items, ensure_ascii=False), ttl=21600)  # 6 小時
    return items


# ─── Bic Camera 日本家電排行 ─────────────────────────

def scrape_bic_camera_ranking(category: str = "beauty", limit: int = 10) -> list:
    """爬 Bic Camera 熱銷排行"""
    cache_key = f"trending:bic_camera:{category}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    items = []
    category_map = {
        "beauty": "01",  # 美容家電
        "kitchen": "02",  # 廚房家電
        "home": "03",     # 生活家電
    }
    cat_id = category_map.get(category, "01")
    url = f"https://www.biccamera.com/bc/c/category/?pid=p_rank_{cat_id}"
    html = _fetch(url)
    if not html:
        return []

    # 解析排行榜
    item_matches = re.findall(
        r'<div[^>]*class="[^"]*item[^"]*"[^>]*>(.*?)</div>\s*</div>',
        html, re.DOTALL
    )
    for i, block in enumerate(item_matches[:limit]):
        name_m = re.search(r'<p[^>]*class="[^"]*bcs_item-name[^"]*"[^>]*>(.*?)</p>', block, re.DOTALL)
        price_m = re.search(r'([\d,]+)\s*円', block)

        if name_m:
            items.append({
                "rank": i + 1,
                "name": _clean_text(name_m.group(1)),
                "price": price_m.group(1) + " 円" if price_m else "",
                "source": "Bic Camera",
                "url": url,
            })

    if items:
        redis_set(cache_key, json.dumps(items, ensure_ascii=False), ttl=86400)
    return items


# ─── 統一接口 ────────────────────────────────────────

def get_trending_souvenirs(country_code: str) -> dict:
    """取得指定國家的熱門伴手禮資料（整合多個來源）"""
    result = {"country": country_code, "sources": []}

    if country_code == "KR":
        oy = scrape_oliveyoung_ranking()
        if oy:
            result["sources"].append({"name": "Olive Young 排行", "items": oy})
        dc = scrape_dcard_travel("korea_travel")
        if dc:
            result["sources"].append({"name": "Dcard 韓國旅遊熱門", "items": dc})

    elif country_code == "JP":
        cm = scrape_cosme_ranking()
        if cm:
            result["sources"].append({"name": "@cosme 排行", "items": cm})
        bc = scrape_bic_camera_ranking("beauty")
        if bc:
            result["sources"].append({"name": "Bic Camera 美容家電", "items": bc})
        dc = scrape_dcard_travel("japan_travel")
        if dc:
            result["sources"].append({"name": "Dcard 日本旅遊熱門", "items": dc})

    return result


def get_trending_idol_events(country_code: str = "") -> list:
    """取得熱門演唱會/見面會（整合 Kpopmap + 原有爬蟲）"""
    events = scrape_kpopmap_events()
    if country_code == "KR":
        # 優先韓國場次
        events = [e for e in events if any(kw in (e.get("city", "") + e.get("venue", "")).lower()
                                            for kw in ["seoul", "korea", "busan", "incheon"])] or events
    elif country_code == "JP":
        events = [e for e in events if any(kw in (e.get("city", "") + e.get("venue", "")).lower()
                                            for kw in ["tokyo", "japan", "osaka", "nagoya"])] or events
    return events


# ─── KKday 熱門活動爬蟲 ──────────────────────────────

# 國家代碼對應 KKday 路徑
_KKDAY_COUNTRY = {
    "JP": "jp", "KR": "kr", "TH": "th",
    "SG": "sg", "VN": "vn", "HK": "hk",
    "MY": "my", "TW": "tw",
}


def scrape_kkday_hot(country_code: str, limit: int = 6) -> list:
    """爬 KKday 指定國家熱門活動"""
    cc = _KKDAY_COUNTRY.get(country_code.upper())
    if not cc:
        return []

    cache_key = f"trending:kkday:{cc}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    url = f"https://www.kkday.com/zh-tw/country/{cc}"
    html = _fetch(url, timeout=15)
    if not html:
        return []

    results = []

    # 嘗試抓 JSON-LD 結構化資料
    ld_matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
    for ld_text in ld_matches:
        try:
            ld = json.loads(ld_text)
            items = ld if isinstance(ld, list) else [ld]
            for item in items:
                if item.get("@type") in ("Product", "TouristAttraction", "Event"):
                    name = item.get("name", "")
                    price = ""
                    offers = item.get("offers", {})
                    if isinstance(offers, dict):
                        price = f"TWD {offers.get('price', '')}"
                    if name:
                        results.append({"title": _clean_text(name), "price": price})
        except Exception:
            continue

    # 備援：抓卡片標題
    if not results:
        # KKday 商品卡片通常在 data-testid 或 class 含 product
        title_patterns = [
            r'class="[^"]*product[^"]*title[^"]*"[^>]*>(.*?)</[^>]+>',
            r'class="[^"]*card[^"]*title[^"]*"[^>]*>(.*?)</[^>]+>',
            r'"productName":"([^"]{5,60})"',
            r'"name":"([^"]{5,60})"',
        ]
        for pat in title_patterns:
            matches = re.findall(pat, html, re.DOTALL | re.IGNORECASE)
            for m in matches:
                title = _clean_text(m)
                if title and len(title) > 4 and not title.startswith("{"):
                    results.append({"title": title, "price": ""})
                    if len(results) >= limit:
                        break
            if results:
                break

    results = results[:limit]
    if results:
        redis_set(cache_key, json.dumps(results, ensure_ascii=False), ttl=43200)
    return results


# ─── Klook 熱門活動爬蟲 ──────────────────────────────

_KLOOK_COUNTRY = {
    "JP": "japan", "KR": "south-korea", "TH": "thailand",
    "SG": "singapore", "VN": "vietnam", "HK": "hong-kong",
    "MY": "malaysia",
}


def scrape_klook_hot(country_code: str, limit: int = 6) -> list:
    """爬 Klook 指定國家熱門活動"""
    cc = _KLOOK_COUNTRY.get(country_code.upper())
    if not cc:
        return []

    cache_key = f"trending:klook:{cc}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    url = f"https://www.klook.com/zh-TW/country/{cc}/"
    html = _fetch(url, timeout=15)
    if not html:
        return []

    results = []

    # 抓 JSON 資料結構
    json_matches = re.findall(r'"activityName"\s*:\s*"([^"]{5,80})"', html)
    for m in json_matches[:limit]:
        title = _clean_text(m)
        if title:
            results.append({"title": title, "price": ""})

    # 備援：抓 h3/h2 標題
    if not results:
        title_matches = re.findall(r'<h[23][^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h[23]>', html, re.DOTALL)
        for m in title_matches[:limit]:
            title = _clean_text(m)
            if title and len(title) > 3:
                results.append({"title": title, "price": ""})

    results = results[:limit]
    if results:
        redis_set(cache_key, json.dumps(results, ensure_ascii=False), ttl=43200)
    return results


def refresh_all():
    """定時任務：刷新所有爬蟲資料"""
    results = {"refreshed": []}

    for name, fn in [
        ("kpopmap", scrape_kpopmap_events),
        ("oliveyoung", scrape_oliveyoung_ranking),
        ("cosme", scrape_cosme_ranking),
        ("dcard_travel", lambda: scrape_dcard_travel("travel")),
        ("dcard_japan", lambda: scrape_dcard_travel("japan_travel")),
        ("dcard_korea", lambda: scrape_dcard_travel("korea_travel")),
        ("bic_beauty", lambda: scrape_bic_camera_ranking("beauty")),
    ]:
        try:
            # 清除快取強制重抓
            from bot.services.redis_store import redis_del
            cache_keys = {
                "kpopmap": "trending:kpopmap_events",
                "oliveyoung": "trending:oliveyoung_ranking",
                "cosme": "trending:cosme_ranking",
                "dcard_travel": "trending:dcard:travel",
                "dcard_japan": "trending:dcard:japan_travel",
                "dcard_korea": "trending:dcard:korea_travel",
                "bic_beauty": "trending:bic_camera:beauty",
            }
            redis_del(cache_keys.get(name, ""))
            items = fn()
            results["refreshed"].append({"source": name, "count": len(items)})
        except Exception as e:
            results["refreshed"].append({"source": name, "error": str(e)})

    return results
