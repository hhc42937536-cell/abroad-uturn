"""
政策自動更新服務 — 簽證 & 海關 & 旅遊警示

架構：
  data/visa_info.json       ← 部署時的基準值（fallback）
  Redis visa:live:{code}    ← 爬蟲抓到的最新值，TTL 8 天
  data/customs_info.json    ← 部署時的基準值（fallback）
  Redis customs:live:{code} ← 爬蟲抓到的最新值，TTL 8 天
  Redis advisory:live:{code}← BOCA RSS 旅遊警示，TTL 8 天

Cron /api/check_policies 每週一執行：
  爬外交部 BOCA 簽證 → 解析 → 存 Redis
  爬各國海關頁面 → 解析 → 存 Redis
  爬外交部 BOCA 旅遊警示 RSS → 解析 → 存 Redis
  完全靜默，不需要人工介入
"""
from __future__ import annotations

import json
import re
import os
import hashlib
import urllib.request
import datetime

from bot.services.redis_store import redis_get, redis_set

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.6",
    "Accept": "text/html,application/xhtml+xml",
}

_DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
)

# 中文國名 → ISO code
_ZH_TO_ISO = {
    "日本": "JP", "韓國": "KR", "南韓": "KR",
    "泰國": "TH", "新加坡": "SG", "越南": "VN",
    "馬來西亞": "MY", "印尼": "ID", "菲律賓": "PH",
    "香港": "HK", "澳門": "MO", "中國": "CN",
    "英國": "GB", "法國": "FR", "德國": "DE",
    "義大利": "IT", "西班牙": "ES", "荷蘭": "NL",
    "奧地利": "AT", "捷克": "CZ", "瑞士": "CH",
    "土耳其": "TR", "美國": "US", "加拿大": "CA",
    "澳洲": "AU", "紐西蘭": "NZ", "阿聯酋": "AE",
    "帛琉": "PW", "關島": "GU", "柬埔寨": "KH",
    "緬甸": "MM",
    # 旅遊警示常見國家（補充）
    "以色列": "IL", "巴勒斯坦": "PS", "伊朗": "IR", "伊拉克": "IQ",
    "阿富汗": "AF", "敘利亞": "SY", "葉門": "YE", "利比亞": "LY",
    "索馬利亞": "SO", "蘇丹": "SD", "南蘇丹": "SS", "剛果": "CD",
    "烏克蘭": "UA", "俄羅斯": "RU", "白俄羅斯": "BY",
    "朝鮮": "KP", "北韓": "KP", "緬甸": "MM", "海地": "HT",
    "委內瑞拉": "VE", "尼加拉瓜": "NI", "薩爾瓦多": "SV",
    "巴基斯坦": "PK", "孟加拉": "BD", "斯里蘭卡": "LK",
    "尼泊爾": "NP", "不丹": "BT", "印度": "IN",
    "埃及": "EG", "突尼西亞": "TN", "摩洛哥": "MA", "阿爾及利亞": "DZ",
    "奈及利亞": "NG", "肯亞": "KE", "衣索比亞": "ET", "坦尚尼亞": "TZ",
    "墨西哥": "MX", "哥倫比亞": "CO", "秘魯": "PE", "巴西": "BR",
    "阿根廷": "AR", "智利": "CL", "厄瓜多": "EC",
    "沙烏地阿拉伯": "SA", "科威特": "KW", "卡達": "QA", "巴林": "BH",
    "約旦": "JO", "黎巴嫩": "LB", "以色列": "IL",
    "哈薩克": "KZ", "烏茲別克": "UZ", "吉爾吉斯": "KG",
    "蒙古": "MN", "台灣": "TW",
    "波蘭": "PL", "羅馬尼亞": "RO", "保加利亞": "BG", "匈牙利": "HU",
    "葡萄牙": "PT", "比利時": "BE", "瑞典": "SE", "挪威": "NO",
    "丹麥": "DK", "芬蘭": "FI", "愛爾蘭": "IE", "希臘": "GR",
    "克羅埃西亞": "HR", "塞爾維亞": "RS", "斯洛維尼亞": "SI",
    "赤道幾內亞": "GQ", "馬達加斯加": "MG", "莫三比克": "MZ",
    "辛巴威": "ZW", "尚比亞": "ZM", "安哥拉": "AO",
    "厄利垂亞": "ER", "吉布地": "DJ", "盧安達": "RW",
    "中非共和國": "CF", "查德": "TD", "馬利": "ML",
    "尼日": "NE", "布吉納法索": "BF", "幾內亞": "GN",
    "獅子山": "SL", "賴比瑞亞": "LR", "象牙海岸": "CI",
    "迦納": "GH", "多哥": "TG", "貝南": "BJ",
    "模里西斯": "MU", "塞席爾": "SC", "馬爾地夫": "MV",
    "斐濟": "FJ", "萬那杜": "VU", "巴布亞紐幾內亞": "PG",
    "東帝汶": "TL", "汶萊": "BN", "寮國": "LA",
}


# ── 工具 ──────────────────────────────────────────────

def _fetch(url: str, timeout: int = 15) -> str | None:
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[policy] Fetch error {url}: {e}")
        return None


def _load_json(filename: str) -> dict:
    try:
        with open(os.path.join(_DATA_DIR, filename), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[policy] 讀取 {filename} 失敗: {e}")
        return {}


def _parse_visa_type(text: str) -> str:
    if any(k in text for k in ["免簽", "免 簽", "免辦簽"]):
        return "免簽"
    if any(k in text for k in ["電子簽", "e-Visa", "eVisa", "電子旅遊授權"]):
        return "電子簽"
    if any(k in text for k in ["落地簽", "抵境簽", "Visa on Arrival"]):
        return "落地簽"
    if any(k in text for k in ["需要簽", "需簽", "申請簽證"]):
        return "需簽"
    return ""


def _parse_stay_days(text: str) -> str:
    m = re.search(r'(\d+)\s*天', text)
    return f"{m.group(1)}天" if m else ""


# ── 旅遊警示爬蟲（外交部 BOCA RSS）──────────────────

_ADVISORY_RSS = "https://www.boca.gov.tw/sp-trwa-rss-1.xml"

# 標題格式：第X級（說明文字）國名
_ADVISORY_LEVEL_RE = re.compile(r'第([一二三四])級[（(]([^）)]+)[）)](.+)')
_LEVEL_MAP = {"一": 1, "二": 2, "三": 3, "四": 4}


def scrape_travel_advisories() -> dict:
    """
    爬外交部 BOCA 旅遊警示 RSS，解析後存入 Redis advisory:live:{code}
    回傳: {"updated": [codes], "unchanged": [codes], "failed": [codes]}
    """
    xml = _fetch(_ADVISORY_RSS)
    if not xml:
        return {"updated": [], "unchanged": [], "failed": ["RSS_FETCH"]}

    today = datetime.date.today().isoformat()
    updated, unchanged, failed = [], [], []

    # 解析 RSS <item> 區塊
    items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL | re.IGNORECASE)
    print(f"[policy] advisory RSS 解析到 {len(items)} 個 item")

    for item in items:
        title_m = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>|<title>(.*?)</title>', item, re.DOTALL)
        if not title_m:
            continue
        title = (title_m.group(1) or title_m.group(2) or "").strip()

        desc_m = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>|<description>(.*?)</description>', item, re.DOTALL)
        summary = ""
        if desc_m:
            raw_desc = (desc_m.group(1) or desc_m.group(2) or "").strip()
            summary = re.sub(r'<[^>]+>', '', raw_desc).strip()[:120]

        m = _ADVISORY_LEVEL_RE.match(title)
        if not m:
            continue

        level_zh, level_text, country_zh = m.group(1), m.group(2), m.group(3).strip()
        level = _LEVEL_MAP.get(level_zh, 0)
        if not level:
            continue

        # 找 ISO code
        iso = _ZH_TO_ISO.get(country_zh)
        if not iso:
            for zh, code in _ZH_TO_ISO.items():
                if zh in country_zh or country_zh in zh:
                    iso = code
                    break
        if not iso:
            continue

        new_data = {
            "level": level,
            "level_text": f"第{level_zh}級（{level_text}）",
            "country": country_zh,
            "summary": summary,
            "updated": today,
        }

        # 比對舊值，有異動才算更新
        existing = redis_get(f"advisory:live:{iso}")
        if existing:
            try:
                old = json.loads(existing)
                if old.get("level") == level:
                    unchanged.append(iso)
                    # 延長 TTL
                    redis_set(f"advisory:live:{iso}", existing, ttl=86400 * 8)
                    continue
            except Exception:
                pass

        redis_set(f"advisory:live:{iso}", json.dumps(new_data, ensure_ascii=False), ttl=86400 * 8)
        updated.append(iso)
        print(f"[policy] advisory {iso}({country_zh}) 更新為 Level {level}")

    print(f"[policy] advisory: 更新 {len(updated)}, 未變 {len(unchanged)}, 失敗 {len(failed)}")
    return {"updated": updated, "unchanged": unchanged, "failed": failed}


# ── 簽證爬蟲（外交部 BOCA）──────────────────────────

_BOCA_BASE = "https://www.boca.gov.tw"

# BOCA 免簽/落地簽/電子簽綜合頁面（2025 改版後的正確 URL）
_BOCA_VISA_EXEMPT_URL = "/cp-220-4486-7785a-1.html"

# 落地簽與電子簽頁面（各有獨立頁面）
_BOCA_VOA_URL = "/cp-220-4489-7785a-1.html"
_BOCA_EVISA_URL = "/cp-220-4490-7785a-1.html"


def _parse_boca_list_page(html: str, visa_type_label: str) -> list[dict]:
    """
    解析 BOCA 改版後的 <ol> 列表頁面。
    頁面結構：<h3>停留XX天</h3> → <ol><li>國名</li>…</ol>
    visa_type_label: "免簽" / "落地簽" / "電子簽"
    """
    results = []
    today = datetime.date.today().isoformat()

    # 把頁面切成段落：找每個「停留N天」區塊
    # 例：<h3...>停留90天</h3>...<ol>...<li>日本</li>...</ol>
    sections = re.split(r'(?=<h[23][^>]*>)', html, flags=re.IGNORECASE)
    for section in sections:
        # 取出天數
        days_m = re.search(r'停留\s*(\d+)\s*天', section)
        stay_days = f"{days_m.group(1)}天" if days_m else ""

        # 取出 <ol> 內所有 <li>
        ol_m = re.search(r'<ol[^>]*>(.*?)</ol>', section, re.DOTALL | re.IGNORECASE)
        if not ol_m:
            continue
        items = re.findall(r'<li[^>]*>(.*?)</li>', ol_m.group(1), re.DOTALL | re.IGNORECASE)
        for item in items:
            name = re.sub(r'<[^>]+>', '', item).strip()
            name = " ".join(name.split())
            if not name:
                continue
            # 對照 ISO code
            iso = _ZH_TO_ISO.get(name)
            if not iso:
                for zh, code in _ZH_TO_ISO.items():
                    if zh in name:
                        iso = code
                        break
            if not iso:
                continue
            results.append({
                "code": iso,
                "visa_required": False if visa_type_label == "免簽" else visa_type_label,
                "stay_limit": stay_days or "依簽證效期",
                "notes": f"{visa_type_label}，停留{stay_days}" if stay_days else visa_type_label,
                "_scraped": today,
            })

    return results


def _scrape_boca_visa_exempt() -> list[dict]:
    """爬 BOCA 免簽/落地簽/電子簽三個頁面，合併回傳"""
    all_results: dict[str, dict] = {}
    today = datetime.date.today().isoformat()

    for path, label in [
        (_BOCA_VISA_EXEMPT_URL, "免簽"),
        (_BOCA_VOA_URL, "落地簽"),
        (_BOCA_EVISA_URL, "電子簽"),
    ]:
        html = _fetch(f"{_BOCA_BASE}{path}")
        if not html:
            print(f"[policy] BOCA {label} 頁面抓取失敗: {path}")
            continue
        items = _parse_boca_list_page(html, label)
        print(f"[policy] BOCA {label} 解析到 {len(items)} 個國家")
        for item in items:
            code = item["code"]
            # 免簽優先（覆蓋落地簽/電子簽）
            if code not in all_results or label == "免簽":
                all_results[code] = item

    return list(all_results.values())


def scrape_and_update_visa() -> dict:
    """
    將 visa_info.json 載入 Redis（確保 Redis 有資料）。
    BOCA 已將免簽清單改為 PDF，HTML 爬蟲不再可靠；
    改以 JSON 為單一資料來源，每週 cron 刷新 TTL。
    回傳: {"loaded": [codes], "skipped": [codes]}
    """
    base_data = _load_json("visa_info.json")
    loaded, skipped = [], []

    for code, info in base_data.items():
        if code == "_meta":
            continue
        # 已有 Redis 資料且包含 _scraped 標記（人工更新過）→ 保留
        existing_raw = redis_get(f"visa:live:{code}")
        if existing_raw:
            try:
                existing = json.loads(existing_raw)
                if existing.get("_scraped"):
                    # 刷新 TTL 但保留內容
                    redis_set(f"visa:live:{code}", existing_raw, ttl=86400 * 8)
                    skipped.append(code)
                    continue
            except Exception:
                pass
        # Redis 無資料或無 _scraped → 從 JSON 載入
        redis_set(f"visa:live:{code}", json.dumps(info, ensure_ascii=False), ttl=86400 * 8)
        loaded.append(code)

    print(f"[policy] visa: 載入 {len(loaded)} 個, TTL 刷新 {len(skipped)} 個")
    return {"loaded": loaded, "skipped": skipped}


# ── 海關爬蟲 ─────────────────────────────────────────

_CUSTOMS_SOURCES = {
    "JP": "https://www.customs.go.jp/english/passenger/index.htm",
    "KR": "https://www.customs.go.kr/english/main.do",
    "TH": "https://www.customs.go.th/content.php?ini_content=passenger001&lang=en",
    "SG": "https://www.customs.gov.sg/individuals/going-through-customs/arrivals/",
    "US": "https://www.cbp.gov/travel/us-citizens/know-before-you-go/prohibited-and-restricted-items",
}


def scrape_and_update_customs() -> dict:
    """
    監控各國海關頁面，若內容有變化就更新 Redis customs:live:{code}
    用頁面 hash 偵測是否有異動，有異動才重新解析
    """
    base_data = _load_json("customs_info.json")
    updated, unchanged, failed = [], [], []

    for code, url in _CUSTOMS_SOURCES.items():
        html = _fetch(url)
        if not html:
            failed.append(code)
            # 把 JSON 資料存進 Redis 確保不是空的
            if not redis_get(f"customs:live:{code}"):
                base = base_data.get(code, {})
                if base:
                    redis_set(f"customs:live:{code}", json.dumps(base, ensure_ascii=False), ttl=86400 * 8)
            continue

        # 頁面指紋（只取前 5000 字，避免廣告/時間戳影響）
        core = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        core = re.sub(r'<style[^>]*>.*?</style>', '', core, flags=re.DOTALL)
        page_hash = hashlib.md5(core[:5000].encode()).hexdigest()
        stored_hash = redis_get(f"customs:hash:{code}")

        if stored_hash == page_hash:
            unchanged.append(code)
            # 延長 TTL（頁面沒變，但要讓 Redis 資料保持有效）
            existing = redis_get(f"customs:live:{code}")
            if existing:
                redis_set(f"customs:live:{code}", existing, ttl=86400 * 8)
            continue

        # 頁面有變化 → 更新 hash + 保留當前解析資料
        redis_set(f"customs:hash:{code}", page_hash, ttl=86400 * 8)

        # 把 JSON 基準資料存進 Redis（加上爬蟲更新時間戳）
        base = dict(base_data.get(code, {}))
        base["_scraped"] = datetime.date.today().isoformat()
        redis_set(f"customs:live:{code}", json.dumps(base, ensure_ascii=False), ttl=86400 * 8)
        updated.append(code)
        print(f"[policy] customs {code} 頁面有異動，已更新 Redis")

    # 沒有爬蟲的國家也確保 Redis 有資料
    for code, base in base_data.items():
        if code in ("_meta", "_taiwan_return") or code in _CUSTOMS_SOURCES:
            continue
        if not redis_get(f"customs:live:{code}"):
            redis_set(f"customs:live:{code}", json.dumps(base, ensure_ascii=False), ttl=86400 * 8)

    print(f"[policy] customs: 更新 {len(updated)}, 未變 {len(unchanged)}, 失敗 {len(failed)}")
    return {"updated": updated, "unchanged": unchanged, "failed": failed}


# ── 主入口 ────────────────────────────────────────────

def run_all_checks() -> dict:
    """Cron 主入口：靜默更新所有政策資料到 Redis"""
    today = datetime.date.today().isoformat()
    print(f"[policy] 開始政策更新 {today}")

    visa_result = scrape_and_update_visa()
    customs_result = scrape_and_update_customs()
    advisory_result = scrape_travel_advisories()

    result = {
        "date": today,
        "visa": visa_result,
        "customs": customs_result,
        "advisory": advisory_result,
    }

    # 把本次結果存 Redis，供 visa_reminder 讀取（TTL 8 天，覆蓋上週）
    redis_set("policy:last_run", json.dumps(result, ensure_ascii=False), ttl=86400 * 8)

    print(f"[policy] 完成 {today}")
    return result


# ── Handler 讀取介面 ──────────────────────────────────

def get_live_visa(country_code: str) -> dict | None:
    """讀取 Redis 即時簽證資料，無則回 None（讓 handler fallback 到 JSON）"""
    cached = redis_get(f"visa:live:{country_code}")
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
    return None


def get_live_customs(country_code: str) -> dict | None:
    """讀取 Redis 即時海關資料"""
    cached = redis_get(f"customs:live:{country_code}")
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
    return None


def get_live_advisory(country_code: str) -> dict | None:
    """
    讀取 Redis 旅遊警示資料
    回傳 {"level": 1-4, "level_text": "第X級...", "country": "...", "summary": "...", "updated": "date"}
    Level 3/4 需在行前須知顯示警告
    """
    cached = redis_get(f"advisory:live:{country_code}")
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass
    return None
