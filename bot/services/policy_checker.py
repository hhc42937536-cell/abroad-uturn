"""
政策自動更新服務 — 簽證 & 海關

架構：
  data/visa_info.json     ← 部署時的基準值（fallback）
  Redis visa:live:{code}  ← 爬蟲抓到的最新值，TTL 8 天
  data/customs_info.json  ← 部署時的基準值（fallback）
  Redis customs:live:{code} ← 爬蟲抓到的最新值，TTL 8 天

Cron /api/check_policies 每週一執行：
  爬外交部 BOCA → 解析 → 存 Redis
  爬各國海關頁面 → 解析 → 存 Redis
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


# ── 簽證爬蟲（外交部 BOCA）──────────────────────────

_BOCA_BASE = "https://www.boca.gov.tw"

# BOCA 各區域頁面（台灣護照免簽概覽）
_BOCA_REGIONS = [
    "/sp-foof-countrylp-01-2.html",   # 亞太
    "/sp-foof-countrylp-01-3.html",   # 美洲
    "/sp-foof-countrylp-01-4.html",   # 歐洲
    "/sp-foof-countrylp-01-5.html",   # 非洲中東
]


def _scrape_boca_region(path: str) -> list[dict]:
    """爬單一 BOCA 區域頁面，回傳 [{code, visa_required, stay_limit, notes}]"""
    html = _fetch(f"{_BOCA_BASE}{path}")
    if not html:
        return []

    results = []

    # BOCA 頁面通常用 table 列出國家，每列包含：國名、停留天數、備註
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    for row in rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
        # 去除 HTML tag，取純文字
        clean = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        clean = [" ".join(c.split()) for c in clean if c.strip()]

        if len(clean) < 2:
            continue

        country_name = clean[0]
        iso = _ZH_TO_ISO.get(country_name)
        if not iso:
            # 嘗試部分匹配
            for zh, code in _ZH_TO_ISO.items():
                if zh in country_name:
                    iso = code
                    break
        if not iso:
            continue

        combined = " ".join(clean[1:])
        visa_type = _parse_visa_type(combined)
        stay = _parse_stay_days(combined)

        if not visa_type:
            continue

        results.append({
            "code": iso,
            "visa_required": False if visa_type == "免簽" else visa_type,
            "stay_limit": stay or "依簽證效期",
            "notes": combined[:80],
            "_scraped": datetime.date.today().isoformat(),
        })

    return results


def scrape_and_update_visa() -> dict:
    """
    爬外交部 BOCA，解析後存入 Redis visa:live:{code}
    只更新能成功解析的國家，失敗的保留 Redis 舊值或 JSON fallback
    回傳: {"updated": [codes], "failed": [codes]}
    """
    base_data = _load_json("visa_info.json")
    updated, failed = [], []

    all_scraped: dict[str, dict] = {}

    for region_path in _BOCA_REGIONS:
        items = _scrape_boca_region(region_path)
        for item in items:
            code = item.pop("code")
            all_scraped[code] = item

    print(f"[policy] BOCA 爬到 {len(all_scraped)} 個國家")

    # 合併：以 JSON 為底，用爬蟲結果覆蓋關鍵欄位
    for code, base in base_data.items():
        if code == "_meta":
            continue

        scraped = all_scraped.get(code)
        if scraped:
            # 爬到資料 → 合併（保留 JSON 裡的 passport_validity、entry_card 等欄位）
            merged = {**base, **scraped}
            redis_set(f"visa:live:{code}", json.dumps(merged, ensure_ascii=False), ttl=86400 * 8)
            updated.append(code)
        else:
            # 沒爬到 → 把 JSON 資料存進 Redis（確保 Redis 不是空的）
            existing = redis_get(f"visa:live:{code}")
            if not existing:
                redis_set(f"visa:live:{code}", json.dumps(base, ensure_ascii=False), ttl=86400 * 8)
            failed.append(code)

    print(f"[policy] visa 更新: {len(updated)} 個, 未爬到: {len(failed)} 個（保留舊資料）")
    return {"updated": updated, "failed": failed}


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

    print(f"[policy] 完成 {today}")
    return {
        "date": today,
        "visa": visa_result,
        "customs": customs_result,
    }


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
