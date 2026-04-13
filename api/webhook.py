"""
LINE Bot Webhook -- 出國優轉 (AbroadUturn)
==========================================
Vercel Serverless Function (Python)
國外旅遊探索 Bot：便宜機票探索、多平台比價、價格追蹤通知

MVP 功能：
  1. 便宜國外探索（Google Explore 風格）
  2. 多平台機票比價
  3. 價格追蹤通知
"""

import json
import os
import re
import hashlib
import hmac
import urllib.request
import urllib.parse
import time
from http.server import BaseHTTPRequestHandler

# ─── 環境變數 ────────────────────────────────────────
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
TRAVELPAYOUTS_TOKEN = os.environ.get("TRAVELPAYOUTS_TOKEN", "")
LINE_BOT_ID = os.environ.get("LINE_BOT_ID", "")

# Supabase 統計（可選）
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Upstash Redis（價格追蹤用）
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN", "")

# Travelpayouts 聯盟 marker（用於產生佣金連結）
TP_MARKER = os.environ.get("TP_MARKER", "abroaduturn")


# ─── 城市 IATA 代碼對照表 ─────────────────────────────
CITY_CODES = {
    # 日本
    "東京": "TYO", "tokyo": "TYO",
    "大阪": "OSA", "osaka": "OSA",
    "名古屋": "NGO",
    "福岡": "FUK",
    "札幌": "CTS",
    "沖繩": "OKA", "那霸": "OKA",
    "京都": "KIX",  # 關西機場
    # 韓國
    "首爾": "SEL", "seoul": "SEL",
    "釜山": "PUS",
    "濟州": "CJU",
    # 東南亞
    "曼谷": "BKK", "bangkok": "BKK",
    "清邁": "CNX",
    "普吉": "HKT", "普吉島": "HKT",
    "新加坡": "SIN", "singapore": "SIN",
    "吉隆坡": "KUL",
    "胡志明": "SGN", "胡志明市": "SGN",
    "河內": "HAN",
    "峇里島": "DPS", "巴里島": "DPS", "峇里": "DPS",
    "馬尼拉": "MNL",
    "宿霧": "CEB",
    "雅加達": "JKT",
    # 港澳中
    "香港": "HKG", "hong kong": "HKG",
    "澳門": "MFM",
    "上海": "SHA",
    "北京": "BJS",
    "廣州": "CAN",
    "深圳": "SZX",
    # 歐洲
    "倫敦": "LON", "london": "LON",
    "巴黎": "PAR", "paris": "PAR",
    "羅馬": "ROM",
    "米蘭": "MIL",
    "巴塞隆納": "BCN",
    "阿姆斯特丹": "AMS",
    "法蘭克福": "FRA",
    "維也納": "VIE",
    "布拉格": "PRG",
    "蘇黎世": "ZRH",
    "伊斯坦堡": "IST",
    # 美洲
    "紐約": "NYC", "new york": "NYC",
    "洛杉磯": "LAX", "la": "LAX",
    "舊金山": "SFO",
    "西雅圖": "SEA",
    "溫哥華": "YVR",
    "多倫多": "YTO",
    # 大洋洲
    "雪梨": "SYD", "sydney": "SYD",
    "墨爾本": "MEL",
    "奧克蘭": "AKL",
    # 其他
    "杜拜": "DXB",
    "帛琉": "ROR",
    "關島": "GUM",
    "亞庇": "BKI",
    "蘭卡威": "LGK",
    "檳城": "PEN",
    "金邊": "PNH",
    "暹粒": "REP",
    "仰光": "RGN",
}

# 城市中文名對照（IATA → 顯示名稱）
IATA_TO_NAME = {
    "TYO": "東京", "OSA": "大阪", "NGO": "名古屋", "FUK": "福岡",
    "CTS": "札幌", "OKA": "沖繩", "KIX": "京都/關西",
    "SEL": "首爾", "PUS": "釜山", "CJU": "濟州",
    "BKK": "曼谷", "CNX": "清邁", "HKT": "普吉島", "SIN": "新加坡",
    "KUL": "吉隆坡", "SGN": "胡志明市", "HAN": "河內",
    "DPS": "峇里島", "MNL": "馬尼拉", "CEB": "宿霧", "JKT": "雅加達",
    "HKG": "香港", "MFM": "澳門", "SHA": "上海", "BJS": "北京",
    "CAN": "廣州", "SZX": "深圳",
    "LON": "倫敦", "PAR": "巴黎", "ROM": "羅馬", "MIL": "米蘭",
    "BCN": "巴塞隆納", "AMS": "阿姆斯特丹", "FRA": "法蘭克福",
    "VIE": "維也納", "PRG": "布拉格", "ZRH": "蘇黎世", "IST": "伊斯坦堡",
    "NYC": "紐約", "LAX": "洛杉磯", "SFO": "舊金山", "SEA": "西雅圖",
    "YVR": "溫哥華", "YTO": "多倫多",
    "SYD": "雪梨", "MEL": "墨爾本", "AKL": "奧克蘭",
    "DXB": "杜拜", "ROR": "帛琉", "GUM": "關島",
    "NRT": "東京成田", "HND": "東京羽田", "ICN": "首爾仁川",
    "BKI": "亞庇", "LGK": "蘭卡威", "PEN": "檳城",
    "PNH": "金邊", "REP": "暹粒", "RGN": "仰光",
}

# 國旗 emoji（IATA 城市碼 → 國旗）
CITY_FLAG = {
    "TYO": "\U0001f1ef\U0001f1f5", "OSA": "\U0001f1ef\U0001f1f5", "NGO": "\U0001f1ef\U0001f1f5",
    "FUK": "\U0001f1ef\U0001f1f5", "CTS": "\U0001f1ef\U0001f1f5", "OKA": "\U0001f1ef\U0001f1f5",
    "KIX": "\U0001f1ef\U0001f1f5", "NRT": "\U0001f1ef\U0001f1f5", "HND": "\U0001f1ef\U0001f1f5",
    "SEL": "\U0001f1f0\U0001f1f7", "PUS": "\U0001f1f0\U0001f1f7", "CJU": "\U0001f1f0\U0001f1f7",
    "ICN": "\U0001f1f0\U0001f1f7",
    "BKK": "\U0001f1f9\U0001f1ed", "CNX": "\U0001f1f9\U0001f1ed", "HKT": "\U0001f1f9\U0001f1ed",
    "SIN": "\U0001f1f8\U0001f1ec", "KUL": "\U0001f1f2\U0001f1fe",
    "SGN": "\U0001f1fb\U0001f1f3", "HAN": "\U0001f1fb\U0001f1f3",
    "DPS": "\U0001f1ee\U0001f1e9", "JKT": "\U0001f1ee\U0001f1e9",
    "MNL": "\U0001f1f5\U0001f1ed", "CEB": "\U0001f1f5\U0001f1ed",
    "HKG": "\U0001f1ed\U0001f1f0", "MFM": "\U0001f1f2\U0001f1f4",
    "SHA": "\U0001f1e8\U0001f1f3", "BJS": "\U0001f1e8\U0001f1f3",
    "CAN": "\U0001f1e8\U0001f1f3", "SZX": "\U0001f1e8\U0001f1f3",
    "LON": "\U0001f1ec\U0001f1e7", "PAR": "\U0001f1eb\U0001f1f7",
    "ROM": "\U0001f1ee\U0001f1f9", "MIL": "\U0001f1ee\U0001f1f9",
    "BCN": "\U0001f1ea\U0001f1f8", "AMS": "\U0001f1f3\U0001f1f1",
    "FRA": "\U0001f1e9\U0001f1ea", "VIE": "\U0001f1e6\U0001f1f9",
    "PRG": "\U0001f1e8\U0001f1ff", "ZRH": "\U0001f1e8\U0001f1ed",
    "IST": "\U0001f1f9\U0001f1f7",
    "NYC": "\U0001f1fa\U0001f1f8", "LAX": "\U0001f1fa\U0001f1f8",
    "SFO": "\U0001f1fa\U0001f1f8", "SEA": "\U0001f1fa\U0001f1f8",
    "YVR": "\U0001f1e8\U0001f1e6", "YTO": "\U0001f1e8\U0001f1e6",
    "SYD": "\U0001f1e6\U0001f1fa", "MEL": "\U0001f1e6\U0001f1fa",
    "AKL": "\U0001f1f3\U0001f1ff",
    "DXB": "\U0001f1e6\U0001f1ea", "ROR": "\U0001f1f5\U0001f1fc",
    "GUM": "\U0001f1ec\U0001f1fa",
    "BKI": "\U0001f1f2\U0001f1fe", "LGK": "\U0001f1f2\U0001f1fe", "PEN": "\U0001f1f2\U0001f1fe",
    "PNH": "\U0001f1f0\U0001f1ed", "REP": "\U0001f1f0\U0001f1ed", "RGN": "\U0001f1f2\U0001f1f2",
}


# ─── LINE API 工具 ────────────────────────────────────

def reply_message(reply_token, messages):
    if not messages:
        return
    if not CHANNEL_ACCESS_TOKEN or not reply_token:
        print(f"[reply] SKIPPED: token={'empty' if not reply_token else 'ok'}")
        return
    data = json.dumps({
        "replyToken": reply_token,
        "messages": messages[:5],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/reply",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[reply] SUCCESS: {resp.status}")
    except Exception as e:
        print(f"[reply] ERROR: {e}")
        if hasattr(e, 'read'):
            print(f"[reply] BODY: {e.read().decode('utf-8', 'ignore')}")


def push_message(user_id: str, messages: list):
    if not messages or not user_id or not CHANNEL_ACCESS_TOKEN:
        return
    data = json.dumps({
        "to": user_id,
        "messages": messages[:5],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[push] SUCCESS: {resp.status}")
    except Exception as e:
        print(f"[push] ERROR: {e}")
        if hasattr(e, 'read'):
            print(f"[push] BODY: {e.read().decode('utf-8', 'ignore')}")


def verify_signature(body: bytes, signature: str) -> bool:
    if not CHANNEL_SECRET:
        return True
    mac = hmac.new(CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256)
    import base64
    return hmac.compare_digest(base64.b64encode(mac.digest()).decode("utf-8"), signature)


def log_usage(user_id: str, feature: str, sub_action: str = None, is_success: bool = True):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        uid_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        data = {"uid_hash": uid_hash, "feature": feature, "is_success": is_success}
        if sub_action:
            data["sub_action"] = sub_action
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/linebot_usage_logs",
            data=body,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"[log] {e}")


# ─── Upstash Redis 工具（價格追蹤用）──────────────────

def _redis_cmd(cmd: list):
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        return None
    try:
        url = f"{UPSTASH_REDIS_URL}"
        data = json.dumps(cmd).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("result")
    except Exception as e:
        print(f"[redis] {e}")
        return None


def redis_set(key: str, value: str, ttl: int = 0):
    if ttl > 0:
        return _redis_cmd(["SET", key, value, "EX", str(ttl)])
    return _redis_cmd(["SET", key, value])


def redis_get(key: str):
    return _redis_cmd(["GET", key])


def redis_keys(pattern: str):
    return _redis_cmd(["KEYS", pattern]) or []


def redis_del(key: str):
    return _redis_cmd(["DEL", key])


# ─── Travelpayouts API ───────────────────────────────

_tp_cache = {}  # 簡單 in-memory 快取

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
    """搜尋某月最便宜的目的地（Google Explore 風格）"""
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
    """搜尋指定路線的航班價格"""
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


# ─── Mock 資料（無 API Token 時使用）─────────────────

def _mock_explore_data(month: str) -> list:
    """模擬 Google Explore 風格的便宜目的地"""
    return [
        {"origin": "TPE", "destination": "NRT", "price": 4280,
         "airline": "MM", "departure_at": f"{month}-15", "return_at": f"{month}-20",
         "transfers": 0, "duration": 210, "duration_to": 210, "duration_back": 225},
        {"origin": "TPE", "destination": "ICN", "price": 3650,
         "airline": "7C", "departure_at": f"{month}-10", "return_at": f"{month}-14",
         "transfers": 0, "duration": 165, "duration_to": 165, "duration_back": 170},
        {"origin": "TPE", "destination": "BKK", "price": 5120,
         "airline": "TG", "departure_at": f"{month}-08", "return_at": f"{month}-13",
         "transfers": 0, "duration": 225, "duration_to": 225, "duration_back": 220},
        {"origin": "TPE", "destination": "DPS", "price": 6800,
         "airline": "CI", "departure_at": f"{month}-12", "return_at": f"{month}-17",
         "transfers": 1, "duration": 420, "duration_to": 420, "duration_back": 430},
        {"origin": "TPE", "destination": "SIN", "price": 5580,
         "airline": "TR", "departure_at": f"{month}-20", "return_at": f"{month}-25",
         "transfers": 0, "duration": 270, "duration_to": 270, "duration_back": 265},
        {"origin": "TPE", "destination": "OSA", "price": 4950,
         "airline": "MM", "departure_at": f"{month}-05", "return_at": f"{month}-10",
         "transfers": 0, "duration": 195, "duration_to": 195, "duration_back": 210},
        {"origin": "TPE", "destination": "HKG", "price": 3280,
         "airline": "CX", "departure_at": f"{month}-18", "return_at": f"{month}-21",
         "transfers": 0, "duration": 105, "duration_to": 105, "duration_back": 115},
        {"origin": "TPE", "destination": "SGN", "price": 4150,
         "airline": "VJ", "departure_at": f"{month}-22", "return_at": f"{month}-27",
         "transfers": 0, "duration": 195, "duration_to": 195, "duration_back": 200},
    ]


def _mock_flight_data(origin: str, dest: str, depart: str, ret: str) -> list:
    """模擬多平台比價結果"""
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


# ─── 航空公司代碼 → 名稱 ─────────────────────────────

AIRLINE_NAMES = {
    "CI": "中華航空", "BR": "長榮航空", "CX": "國泰航空",
    "SQ": "新加坡航空", "TG": "泰國航空", "JL": "日本航空",
    "NH": "全日空", "KE": "大韓航空", "OZ": "韓亞航空",
    "MM": "樂桃航空", "TR": "酷航", "7C": "濟州航空",
    "IT": "台灣虎航", "VJ": "越捷航空", "AK": "亞洲航空",
    "FD": "泰亞洲航空", "3K": "捷星亞洲", "HX": "香港航空",
    "UO": "香港快運", "HX": "香港航空", "D7": "亞洲航空X", "PR": "菲律賓航空",
    "5J": "宿霧太平洋", "GA": "嘉魯達航空", "MH": "馬航",
    "EK": "阿聯酋", "QF": "澳航", "NZ": "紐航",
    "UA": "聯合航空", "DL": "達美航空", "AA": "美國航空",
    "BA": "英國航空", "AF": "法國航空", "LH": "漢莎航空",
    "TK": "土耳其航空", "QR": "卡達航空",
}


def _airline_name(code: str) -> str:
    return AIRLINE_NAMES.get(code, code)


def _duration_str(minutes: int) -> str:
    if minutes <= 0:
        return ""
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def _tp_booking_url(origin: str, dest: str, depart: str, ret: str = "", link: str = "") -> str:
    """產生 Travelpayouts 聯盟購票連結（Aviasales 搜尋頁）
    如果 API 回傳了 link 欄位，優先使用（含精確航班資訊）；
    否則自動產生搜尋連結。
    """
    if link:
        # API 回傳的 link 格式: /search/TPE0406TYO1?t=...
        return f"https://www.aviasales.com{link}&marker={TP_MARKER}"
    # Fallback: 自動產生搜尋連結
    # 格式: TPE0506NRT1 (origin + DDMM + dest + passengers)
    if len(depart) >= 10:
        dd = depart[8:10]
        mm = depart[5:7]
    else:
        dd = "01"
        mm = depart[5:7] if len(depart) >= 7 else "01"
    route = f"{origin}{dd}{mm}{dest}"
    if ret and len(ret) >= 10:
        rd = ret[8:10]
        rm = ret[5:7]
        route += f"{rd}{rm}"
    return f"https://www.aviasales.com/search/{route}1?marker={TP_MARKER}"


def _google_flights_url(origin: str, dest: str, depart: str, ret: str = "") -> str:
    """產生 Google Flights 搜尋連結"""
    # 格式: https://www.google.com/travel/flights?q=TPE+to+NRT+2026-06-15&hl=zh-TW
    q = f"flights from {origin} to {dest}"
    if depart:
        q += f" {depart}"
    if ret:
        q += f" to {ret}"
    params = urllib.parse.urlencode({"q": q, "hl": "zh-TW", "curr": "TWD"})
    return f"https://www.google.com/travel/flights?{params}"


def _google_explore_url(origin: str = "TPE") -> str:
    """產生 Google Travel Explore 連結（地圖探索最便宜）"""
    return f"https://www.google.com/travel/explore?hl=zh-TW&curr=TWD"


# ─── Flex Message 建構 ───────────────────────────────

def _flight_bubble(flight: dict, rank: int = 0, show_track_btn: bool = True) -> dict:
    """建立單張航班 Flex Bubble"""
    dest = flight.get("destination", "")
    city_name = IATA_TO_NAME.get(dest, dest)
    flag = CITY_FLAG.get(dest, "\u2708\ufe0f")
    price = flight.get("price", 0)
    airline = _airline_name(flight.get("airline", ""))
    depart = flight.get("departure_at", "")
    ret = flight.get("return_at", "")
    transfers = flight.get("transfers", 0)
    dur_to = flight.get("duration_to", flight.get("duration", 0))

    transfer_text = "\u2708\ufe0f \u76f4\u98db" if transfers == 0 else f"\U0001f504 \u8f49\u6a5f{transfers}\u6b21"
    duration_text = _duration_str(dur_to)

    # Header 顏色（排名用）
    header_colors = ["#FF6B35", "#2196F3", "#4CAF50", "#9C27B0", "#FF9800"]
    header_bg = header_colors[rank % len(header_colors)]

    # 排名標籤
    rank_labels = ["\U0001f947 \u6700\u4f4e\u50f9", "\U0001f948 \u7b2c\u4e8c\u4f4e", "\U0001f949 \u7b2c\u4e09", "", ""]
    rank_text = rank_labels[rank] if rank < len(rank_labels) else ""

    header_contents = []
    if rank_text:
        header_contents.append({
            "type": "text", "text": rank_text,
            "color": "#FFFFFF", "size": "xs", "weight": "bold",
        })
    header_contents.append({
        "type": "text", "text": f"{flag} {city_name} ({dest})",
        "color": "#FFFFFF", "weight": "bold", "size": "lg",
    })

    # 日期格式化
    date_display = ""
    if depart:
        d = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
        date_display = f"\U0001f4c5 {d}"
        if ret:
            r = ret[5:].replace("-", "/") if len(ret) >= 10 else ret
            date_display += f" \u2192 {r}"

    body_contents = [
        {
            "type": "text",
            "text": f"NT$ {price:,} \u542b\u7a05",
            "size": "xl", "weight": "bold", "color": "#E53935",
        },
        {"type": "separator", "margin": "md"},
    ]
    if date_display:
        body_contents.append({
            "type": "text", "text": date_display,
            "size": "sm", "color": "#555555", "margin": "md",
        })
    # 平台來源（gate）
    gate = flight.get("gate", "")
    airline_gate = f"\u2708\ufe0f {airline}"
    if gate:
        airline_gate += f" \u00b7 {gate}"
    airline_gate += f" \u00b7 {transfer_text}"

    body_contents.append({
        "type": "text",
        "text": airline_gate,
        "size": "sm", "color": "#555555", "margin": "sm", "wrap": True,
    })
    if duration_text:
        body_contents.append({
            "type": "text",
            "text": f"\u23f1\ufe0f {duration_text}",
            "size": "sm", "color": "#888888", "margin": "sm",
        })

    # Footer 按鈕
    origin = flight.get("origin", "TPE")
    link = flight.get("link", "")
    booking_url = _tp_booking_url(origin, dest, depart, ret, link=link)

    google_url = _google_flights_url(origin, dest, depart, ret)

    footer_contents = [
        {
            "type": "button", "style": "primary", "color": "#FF6B35",
            "height": "sm",
            "action": {"type": "uri", "label": "\U0001f50d \u8a02\u7968\u00b7Aviasales", "uri": booking_url},
        },
        {
            "type": "button", "style": "primary", "color": "#4285F4",
            "height": "sm",
            "action": {"type": "uri", "label": "\U0001f310 Google Flights \u6bd4\u50f9", "uri": google_url},
        },
    ]
    if show_track_btn:
        track_data = f"\u8ffd\u8e64|{origin}|{dest}|{depart}|{ret}"
        footer_contents.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": "\U0001f4e2 \u8ffd\u8e64\u964d\u50f9\u901a\u77e5", "text": track_data},
        })

    return {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_bg,
            "paddingAll": "15px",
            "contents": header_contents,
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "15px",
            "contents": body_contents,
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "10px",
            "contents": footer_contents,
        },
    }


def _month_picker_flex() -> list:
    """建立月份選擇器 Flex Carousel（漂亮版）"""
    import datetime
    today = datetime.date.today()

    bubbles = []
    month_names = ["1月", "2月", "3月", "4月", "5月", "6月",
                   "7月", "8月", "9月", "10月", "11月", "12月"]
    month_themes = [
        # (背景色, emoji, 一句話描述)
        ("#4FC3F7", "\u2744\ufe0f", "冬季特惠"),      # 1月
        ("#F48FB1", "\U0001f338", "早春賞花"),         # 2月
        ("#CE93D8", "\U0001f338", "櫻花季節"),         # 3月
        ("#81C784", "\U0001f30f", "說走就走"),         # 4月
        ("#FFD54F", "\u2600\ufe0f", "初夏出遊"),       # 5月
        ("#FF8A65", "\u2600\ufe0f", "暑假開跑"),       # 6月
        ("#4DD0E1", "\U0001f3d6\ufe0f", "海島度假"),   # 7月
        ("#4DB6AC", "\U0001f3d6\ufe0f", "盛夏旅行"),   # 8月
        ("#FFB74D", "\U0001f341", "秋季旅遊"),         # 9月
        ("#FF8A65", "\U0001f341", "賞楓季節"),         # 10月
        ("#A1887F", "\U0001f342", "深秋優惠"),         # 11月
        ("#90A4AE", "\u2744\ufe0f", "跨年搶票"),       # 12月
    ]

    for i in range(6):
        y = today.year + (today.month + i - 1) // 12
        m = (today.month + i - 1) % 12 + 1
        month_str = f"{y}-{m:02d}"
        bg_color, emoji, desc = month_themes[m - 1]
        name = month_names[m - 1]

        bubbles.append({
            "type": "bubble",
            "size": "micro",
            "styles": {
                "body": {"backgroundColor": bg_color},
            },
            "body": {
                "type": "box", "layout": "vertical",
                "justifyContent": "center",
                "alignItems": "center",
                "paddingAll": "18px",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": emoji, "size": "4xl", "align": "center"},
                    {"type": "text", "text": f"{y}",
                     "size": "xxs", "color": "#FFFFFFBB", "align": "center", "margin": "md"},
                    {"type": "text", "text": name,
                     "size": "xl", "weight": "bold", "color": "#FFFFFF", "align": "center"},
                    {"type": "text", "text": desc,
                     "size": "xs", "color": "#FFFFFFDD", "align": "center"},
                    {"type": "box", "layout": "vertical",
                     "backgroundColor": "#FFFFFF33", "cornerRadius": "md",
                     "paddingAll": "8px", "margin": "md",
                     "contents": [
                         {"type": "text", "text": "\u2708\ufe0f \u9ede\u6211\u63a2\u7d22",
                          "size": "sm", "color": "#FFFFFF", "align": "center", "weight": "bold"},
                     ]},
                ],
                "action": {
                    "type": "message",
                    "label": name,
                    "text": f"\u63a2\u7d22|{month_str}",
                },
            },
        })

    return [
        {"type": "text", "text": "\U0001f30d \u9078\u64c7\u51fa\u767c\u6708\u4efd\uff0c\u5e6b\u4f60\u627e\u6700\u4fbf\u5b9c\u7684\u76ee\u7684\u5730\uff01"},
        {
            "type": "flex",
            "altText": "\u9078\u64c7\u51fa\u767c\u6708\u4efd",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


# ─── 日期解析工具 ─────────────────────────────────────

def _parse_date_range(text: str) -> tuple:
    """
    解析日期範圍，支援多種格式：
    - "6/15-6/20" → ("2026-06-15", "2026-06-20")
    - "6/15~6/20" → ("2026-06-15", "2026-06-20")
    - "2026-06-15 2026-06-20" → ("2026-06-15", "2026-06-20")
    - "6月15到20" → ("2026-06-15", "2026-06-20")
    """
    import datetime
    today = datetime.date.today()
    year = today.year

    # 格式: 6/15-6/20 或 6/15~6/20
    m = re.search(r"(\d{1,2})/(\d{1,2})\s*[-~]\s*(\d{1,2})/(\d{1,2})", text)
    if m:
        m1, d1, m2, d2 = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        y1 = year if m1 >= today.month else year + 1
        y2 = year if m2 >= today.month else year + 1
        return (f"{y1}-{m1:02d}-{d1:02d}", f"{y2}-{m2:02d}-{d2:02d}")

    # 格式: 2026-06-15 到/- 2026-06-20
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*[-~到]\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        return (m.group(1), m.group(2))

    # 格式: 6月15到20 或 6月15-20
    m = re.search(r"(\d{1,2})\u6708(\d{1,2})\s*[-~到]\s*(\d{1,2})", text)
    if m:
        mon, d1, d2 = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = year if mon >= today.month else year + 1
        return (f"{y}-{mon:02d}-{d1:02d}", f"{y}-{mon:02d}-{d2:02d}")

    # 只有一個日期
    m = re.search(r"(\d{1,2})/(\d{1,2})", text)
    if m:
        mon, day = int(m.group(1)), int(m.group(2))
        y = year if mon >= today.month else year + 1
        return (f"{y}-{mon:02d}-{day:02d}", "")

    return ("", "")


def _parse_destination(text: str) -> str:
    """從文字中解析目的地 IATA 碼"""
    text_lower = text.lower().strip()
    # 先查完整匹配
    for name, code in CITY_CODES.items():
        if name in text_lower:
            return code
    # 查 IATA 碼（3 字母大寫）
    m = re.search(r"\b([A-Z]{3})\b", text)
    if m:
        return m.group(1)
    return ""


# ─── 主要功能 handler ─────────────────────────────────

def handle_quick_explore(origin: str = "TPE") -> list:
    """Google Explore 風格：直接秀熱門目的地 + 近期最低價"""
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = _tp_api("prices_for_dates", {
            "origin": origin,
            "sorting": "price",
            "limit": 50,
            "one_way": "false",
        })

    if not flights:
        flights = _mock_explore_data("2026-05")

    if not flights:
        return [{"type": "text", "text": "找不到便宜航班，請稍後再試 \U0001f64f"}]

    # 去重（同目的地只保留最便宜）
    seen = {}
    for f in flights:
        dest = f.get("destination", "")
        if dest and (dest not in seen or f.get("price", 99999) < seen[dest].get("price", 99999)):
            seen[dest] = f
    unique = sorted(seen.values(), key=lambda x: x.get("price", 99999))[:10]

    bubbles = [_flight_bubble(f, i) for i, f in enumerate(unique)]

    # 最後加 Google Explore 卡片
    bubbles.append({
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical",
            "justifyContent": "center", "alignItems": "center",
            "paddingAll": "20px", "spacing": "md",
            "contents": [
                {"type": "text", "text": "\U0001f310", "size": "3xl", "align": "center"},
                {"type": "text", "text": "想看更多？", "weight": "bold", "size": "lg", "align": "center"},
                {"type": "text", "text": "用 Google 探索全球最便宜目的地",
                 "size": "sm", "color": "#888888", "align": "center", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px", "spacing": "sm",
            "contents": [
                {"type": "button", "style": "primary", "color": "#4285F4",
                 "action": {"type": "uri", "label": "Google Travel Explore",
                            "uri": _google_explore_url()}},
                {"type": "button", "style": "secondary",
                 "action": {"type": "message", "label": "\U0001f4c5 選特定月份探索",
                            "text": "探索最便宜"}},
            ],
        },
    })

    return [
        {"type": "text", "text": "\u2708\ufe0f \u53f0\u5317\u51fa\u767c\uff0c\u8fd1\u671f\u6700\u4fbf\u5b9c\u7684\u76ee\u7684\u5730\uff1a"},
        {
            "type": "flex",
            "altText": "近期最便宜目的地",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def handle_explore(month: str, origin: str = "TPE") -> list:
    """功能 1: 便宜國外探索"""
    # 嘗試真 API，失敗就用 Mock
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_cheapest_by_month(origin, month)

    if not flights:
        flights = _mock_explore_data(month)
        print(f"[explore] Using MOCK data for {month}")

    if not flights:
        return [{"type": "text", "text": f"\u627e\u4e0d\u5230 {month} \u7684\u4fbf\u5b9c\u822a\u73ed\uff0c\u8acb\u8a66\u8a66\u5176\u4ed6\u6708\u4efd \U0001f64f"}]

    # 去重（同目的地只保留最便宜）
    seen = {}
    for f in flights:
        dest = f.get("destination", "")
        if dest not in seen or f.get("price", 99999) < seen[dest].get("price", 99999):
            seen[dest] = f
    unique = sorted(seen.values(), key=lambda x: x.get("price", 99999))[:10]

    bubbles = [_flight_bubble(f, i) for i, f in enumerate(unique)]

    # 最後加一張 Google Explore 卡片
    google_explore = {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical",
            "justifyContent": "center",
            "alignItems": "center",
            "paddingAll": "20px",
            "spacing": "md",
            "contents": [
                {"type": "text", "text": "\U0001f310", "size": "3xl", "align": "center"},
                {"type": "text", "text": "\u60f3\u770b\u66f4\u591a\uff1f", "weight": "bold",
                 "size": "lg", "align": "center"},
                {"type": "text", "text": "\u7528 Google \u63a2\u7d22\u5168\u7403\u6700\u4fbf\u5b9c\u76ee\u7684\u5730",
                 "size": "sm", "color": "#888888", "align": "center", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px",
            "contents": [
                {"type": "button", "style": "primary", "color": "#4285F4",
                 "action": {"type": "uri", "label": "Google Travel Explore",
                            "uri": _google_explore_url()}},
            ],
        },
    }
    bubbles.append(google_explore)

    month_display = month[5:] if len(month) >= 7 else month
    return [{
        "type": "flex",
        "altText": f"{month_display}\u6708\u6700\u4fbf\u5b9c\u822a\u73ed",
        "contents": {"type": "carousel", "contents": bubbles},
    }]


def handle_compare(text: str, origin: str = "TPE") -> list:
    """功能 2: 多平台機票比價"""
    dest_code = _parse_destination(text)
    if not dest_code:
        return [{"type": "text", "text":
            "\u8acb\u544a\u8a34\u6211\u76ee\u7684\u5730\u548c\u65e5\u671f\uff0c\u4f8b\u5982\uff1a\n"
            "\u300c\u6771\u4eac 6/15-6/20\u300d\n"
            "\u300c\u9996\u723e 7\u670810\u523020\u300d\n"
            "\u300c\u66fc\u8c37 2026-08-01~2026-08-07\u300d\n\n"
            "\U0001f4a1 \u652f\u63f4\u7684\u76ee\u7684\u5730\uff1a\u65e5\u672c\u3001\u97d3\u570b\u3001\u6771\u5357\u4e9e\u3001\u6e2f\u6fb3\u3001\u6b50\u7f8e\u7b49 50+ \u57ce\u5e02"
        }]

    depart, ret = _parse_date_range(text)
    if not depart:
        city_name = IATA_TO_NAME.get(dest_code, dest_code)
        return [{"type": "text", "text":
            f"\u76ee\u7684\u5730\uff1a{city_name} ({dest_code}) \u2705\n\n"
            f"\u8acb\u518d\u544a\u8a34\u6211\u65e5\u671f\uff0c\u4f8b\u5982\uff1a\n"
            f"\u300c{city_name} 6/15-6/20\u300d"
        }]

    # 查詢航班
    flights = None
    if TRAVELPAYOUTS_TOKEN:
        flights = search_flights(origin, dest_code, depart, ret)

    if not flights:
        flights = _mock_flight_data(origin, dest_code, depart, ret)
        print(f"[compare] Using MOCK data for {origin}-{dest_code}")

    if not flights:
        return [{"type": "text", "text": f"\u627e\u4e0d\u5230 {IATA_TO_NAME.get(dest_code, dest_code)} \u7684\u822a\u73ed\uff0c\u8acb\u8a66\u5176\u4ed6\u65e5\u671f \U0001f64f"}]

    flights.sort(key=lambda x: x.get("price", 99999))
    top = flights[:6]
    bubbles = [_flight_bubble(f, i) for i, f in enumerate(top)]

    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    d_short = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
    r_short = ret[5:].replace("-", "/") if ret and len(ret) >= 10 else ""
    date_text = f"{d_short}" + (f"~{r_short}" if r_short else "")

    return [{
        "type": "flex",
        "altText": f"{city_name} {date_text} \u6a5f\u7968\u6bd4\u50f9",
        "contents": {"type": "carousel", "contents": bubbles},
    }]


def handle_track(user_id: str, data: str) -> list:
    """功能 3: 設定價格追蹤"""
    # 格式: "追蹤|TPE|TYO|2026-06-15|2026-06-20"
    parts = data.split("|")
    if len(parts) < 4:
        return [{"type": "text", "text": "\u8ffd\u8e64\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u5f9e\u822a\u73ed\u5361\u7247\u9ede\u300c\u8ffd\u8e64\u964d\u50f9\u901a\u77e5\u300d\u6309\u9215 \U0001f64f"}]

    origin = parts[1]
    dest = parts[2]
    depart = parts[3]
    ret = parts[4] if len(parts) > 4 else ""
    city_name = IATA_TO_NAME.get(dest, dest)

    # 儲存到 Redis
    route_key = f"{origin}_{dest}_{depart}_{ret}"
    track_key = f"track:{user_id}:{route_key}"
    track_data = json.dumps({
        "origin": origin,
        "destination": dest,
        "depart": depart,
        "return": ret,
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "last_price": 0,
    })

    if UPSTASH_REDIS_URL:
        redis_set(track_key, track_data, ttl=86400 * 30)  # 30 天過期
        return [{"type": "text", "text":
            f"\u2705 \u5df2\u8a2d\u5b9a\u8ffd\u8e64\uff01\n\n"
            f"\U0001f6e9\ufe0f {IATA_TO_NAME.get(origin, origin)} \u2192 {city_name}\n"
            f"\U0001f4c5 {depart}" + (f" ~ {ret}" if ret else "") + "\n\n"
            f"\u6bcf\u5929\u5e6b\u4f60\u67e5\u6700\u4f4e\u50f9\uff0c\u964d\u50f9\u6703\u7acb\u523b\u901a\u77e5\u4f60 \U0001f4b0\n"
            f"\u53d6\u6d88\u8ffd\u8e64\u8acb\u8f38\u5165\u300c\u53d6\u6d88\u8ffd\u8e64 {city_name}\u300d"
        }]
    else:
        return [{"type": "text", "text":
            f"\u26a0\ufe0f \u8ffd\u8e64\u529f\u80fd\u5c1a\u672a\u555f\u7528\uff08\u9700\u8981 Redis \u8a2d\u5b9a\uff09\n\n"
            f"\u4f60\u53ef\u4ee5\u5148\u5132\u5b58\u9019\u500b\u641c\u5c0b\uff1a\n"
            f"{IATA_TO_NAME.get(origin, origin)} \u2192 {city_name}\n"
            f"{depart}" + (f" ~ {ret}" if ret else "")
        }]


def handle_cancel_track(user_id: str, text: str) -> list:
    """取消價格追蹤"""
    if not UPSTASH_REDIS_URL:
        return [{"type": "text", "text": "\u8ffd\u8e64\u529f\u80fd\u5c1a\u672a\u555f\u7528"}]

    # 找到使用者的所有追蹤
    keys = redis_keys(f"track:{user_id}:*")
    if not keys:
        return [{"type": "text", "text": "\u4f60\u76ee\u524d\u6c92\u6709\u8ffd\u8e64\u4efb\u4f55\u8def\u7dda \U0001f60a"}]

    # 解析要取消的目的地
    dest_name = text.replace("\u53d6\u6d88\u8ffd\u8e64", "").strip()
    dest_code = ""
    for name, code in CITY_CODES.items():
        if name in dest_name:
            dest_code = code
            break

    deleted = 0
    for key in keys:
        if dest_code and dest_code not in key:
            continue
        redis_del(key)
        deleted += 1

    if deleted:
        return [{"type": "text", "text": f"\u2705 \u5df2\u53d6\u6d88 {deleted} \u500b\u8ffd\u8e64\u9805\u76ee"}]
    return [{"type": "text", "text": f"\u627e\u4e0d\u5230\u300c{dest_name}\u300d\u7684\u8ffd\u8e64\u9805\u76ee"}]


def handle_my_tracks(user_id: str) -> list:
    """查看我的追蹤清單"""
    if not UPSTASH_REDIS_URL:
        return [{"type": "text", "text": "\u8ffd\u8e64\u529f\u80fd\u5c1a\u672a\u555f\u7528"}]

    keys = redis_keys(f"track:{user_id}:*")
    if not keys:
        return [{"type": "text", "text":
            "\u4f60\u76ee\u524d\u6c92\u6709\u8ffd\u8e64\u4efb\u4f55\u8def\u7dda\n\n"
            "\U0001f4a1 \u5728\u63a2\u7d22\u6216\u6bd4\u50f9\u7d50\u679c\u4e2d\uff0c\u9ede\u300c\U0001f4e2 \u8ffd\u8e64\u964d\u50f9\u901a\u77e5\u300d\u5c31\u80fd\u958b\u59cb\u8ffd\u8e64\uff01"
        }]

    lines = ["\U0001f514 \u4f60\u7684\u8ffd\u8e64\u6e05\u55ae\uff1a\n"]
    for key in keys[:10]:
        data = redis_get(key)
        if data:
            try:
                info = json.loads(data)
                origin_name = IATA_TO_NAME.get(info["origin"], info["origin"])
                dest_name = IATA_TO_NAME.get(info["destination"], info["destination"])
                lines.append(f"\u2708\ufe0f {origin_name} \u2192 {dest_name}")
                lines.append(f"   \U0001f4c5 {info['depart']}" +
                             (f" ~ {info['return']}" if info.get("return") else ""))
                if info.get("last_price"):
                    lines.append(f"   \U0001f4b0 \u6700\u65b0\u50f9: NT${info['last_price']:,}")
                lines.append("")
            except Exception:
                pass

    lines.append("\u8f38\u5165\u300c\u53d6\u6d88\u8ffd\u8e64 \u57ce\u5e02\u540d\u300d\u53ef\u53d6\u6d88")
    return [{"type": "text", "text": "\n".join(lines)}]


# ─── 歡迎訊息 ────────────────────────────────────────

def build_welcome_message() -> list:
    return [{
        "type": "flex",
        "altText": "\u6b61\u8fce\u4f86\u5230\u51fa\u570b\u512a\u8f49\uff01",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#FF6B35",
                "paddingAll": "20px",
                "contents": [
                    {"type": "text", "text": "\u2708\ufe0f \u6b61\u8fce\u4f86\u5230\u51fa\u570b\u512a\u8f49\uff01",
                     "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "AbroadUturn - \u4f60\u7684\u667a\u6167\u65c5\u904a\u52a9\u7406",
                     "color": "#FFE0CC", "size": "sm", "margin": "sm"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "lg", "paddingAll": "20px",
                "contents": [
                    {"type": "text", "text": "\U0001f30d \u6211\u80fd\u5e6b\u4f60\u505a\u4ec0\u9ebc\uff1f",
                     "weight": "bold", "size": "md"},
                    {"type": "separator"},
                    {"type": "text", "text":
                        "\u2705 \u63a2\u7d22\u6700\u4fbf\u5b9c\u7684\u51fa\u570b\u76ee\u7684\u5730\n"
                        "\u2705 \u591a\u5e73\u53f0\u6a5f\u7968\u6bd4\u50f9\uff08\u542b\u7a05\u50f9\uff09\n"
                        "\u2705 \u50f9\u683c\u964d\u5e45\u5373\u6642\u901a\u77e5\n"
                        "\u2705 \u76f4\u98db / \u8f49\u6a5f\u7be9\u9078",
                     "size": "sm", "color": "#555555", "wrap": True},
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "15px",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#FF6B35",
                     "action": {"type": "message", "label": "\U0001f30d \u63a2\u7d22\u6700\u4fbf\u5b9c",
                                "text": "\u63a2\u7d22\u6700\u4fbf\u5b9c"}},
                    {"type": "button", "style": "secondary",
                     "action": {"type": "message", "label": "\u2708\ufe0f \u6a5f\u7968\u6bd4\u50f9",
                                "text": "\u6a5f\u7968\u6bd4\u50f9"}},
                    {"type": "button", "style": "secondary",
                     "action": {"type": "message", "label": "\U0001f4a1 \u67e5\u770b\u4f7f\u7528\u6559\u5b78",
                                "text": "\u4f7f\u7528\u6559\u5b78"}},
                ],
            },
        },
    }]


def build_help_message() -> list:
    return [{"type": "text", "text":
        "\u2708\ufe0f \u51fa\u570b\u512a\u8f49 \u4f7f\u7528\u6559\u5b78\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\U0001f30d \u4fbf\u5b9c\u570b\u5916\u63a2\u7d22\n"
        "\u8f38\u5165\u300c\u63a2\u7d22\u6700\u4fbf\u5b9c\u300d\n"
        "\u2192 \u9078\u6708\u4efd \u2192 \u770b\u6700\u4fbf\u5b9c\u76ee\u7684\u5730\n\n"
        "\u2708\ufe0f \u6a5f\u7968\u6bd4\u50f9\n"
        "\u76f4\u63a5\u8f38\u5165\u76ee\u7684\u5730\u548c\u65e5\u671f\uff0c\u4f8b\u5982\uff1a\n"
        "\u300c\u6771\u4eac 6/15-6/20\u300d\n"
        "\u300c\u9996\u723e 7\u670810\u523020\u300d\n\n"
        "\U0001f514 \u50f9\u683c\u8ffd\u8e64\n"
        "\u5728\u822a\u73ed\u5361\u7247\u9ede\u300c\U0001f4e2 \u8ffd\u8e64\u964d\u50f9\u901a\u77e5\u300d\n"
        "\u8f38\u5165\u300c\u6211\u7684\u8ffd\u8e64\u300d\u67e5\u770b\u6e05\u55ae\n"
        "\u8f38\u5165\u300c\u53d6\u6d88\u8ffd\u8e64 \u57ce\u5e02\u540d\u300d\u53d6\u6d88\n\n"
        "\U0001f4a1 \u5c0f\u6280\u5de7\n"
        "\u2022 \u6240\u6709\u50f9\u683c\u90fd\u662f\u300c\u542b\u7a05\u7e3d\u50f9\u300d\n"
        "\u2022 \u9ede\u300c\u67e5\u770b\u8a73\u60c5\u300d\u76f4\u63a5\u8df3\u8f49\u8a02\u7968\u9801"
    }]


# ─── 出發地設定 ──────────────────────────────────────

# 台灣機場 IATA
TW_AIRPORTS = {
    "台北": "TPE", "桃園": "TPE", "松山": "TSA",
    "高雄": "KHH", "小港": "KHH",
    "台中": "RMQ", "清泉崗": "RMQ",
    "台南": "TNN",
    "花蓮": "HUN",
}


def _get_user_origin(user_id: str) -> str:
    """取得使用者設定的出發地（預設 TPE）"""
    if not UPSTASH_REDIS_URL or not user_id:
        return "TPE"
    origin = redis_get(f"origin:{user_id}")
    return origin if origin else "TPE"


def handle_set_origin(user_id: str, text: str) -> list:
    """設定出發機場"""
    city = text.replace("出發地", "").replace("設定", "").replace("改", "").strip()

    if not city:
        # 顯示選擇器
        current = _get_user_origin(user_id)
        current_name = {v: k for k, v in TW_AIRPORTS.items()}.get(current, current)
        buttons = []
        for name, code in [("台北 桃園", "TPE"), ("高雄 小港", "KHH"), ("台中 清泉崗", "RMQ"), ("台南", "TNN")]:
            marker = " \u2705" if code == current else ""
            buttons.append({
                "type": "button",
                "style": "primary" if code == current else "secondary",
                "height": "sm",
                "action": {"type": "message", "label": f"{name}{marker}", "text": f"出發地 {name.split()[0]}"},
            })
        return [{
            "type": "flex",
            "altText": "設定出發機場",
            "contents": {
                "type": "bubble", "size": "kilo",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "\U0001f6eb \u8a2d\u5b9a\u51fa\u767c\u6a5f\u5834",
                         "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                        {"type": "text", "text": f"\u76ee\u524d\uff1a{current_name} ({current})",
                         "color": "#FFE0CC", "size": "sm"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": buttons,
                },
            },
        }]

    # 解析城市
    code = TW_AIRPORTS.get(city)
    if not code:
        return [{"type": "text", "text":
            f"\u627e\u4e0d\u5230\u300c{city}\u300d\u7684\u6a5f\u5834\n\n"
            f"\u652f\u63f4\u7684\u51fa\u767c\u5730\uff1a\u53f0\u5317\u3001\u9ad8\u96c4\u3001\u53f0\u4e2d\u3001\u53f0\u5357\n"
            f"\u4f8b\u5982\uff1a\u300c\u51fa\u767c\u5730 \u9ad8\u96c4\u300d"
        }]

    # 儲存
    if UPSTASH_REDIS_URL and user_id:
        redis_set(f"origin:{user_id}", code, ttl=86400 * 365)

    city_name = {v: k for k, v in TW_AIRPORTS.items()}.get(code, city)
    return [{"type": "text", "text":
        f"\u2705 \u51fa\u767c\u5730\u5df2\u8a2d\u5b9a\u70ba\uff1a{city} ({code})\n\n"
        f"\u4ee5\u5f8c\u641c\u5c0b\u90fd\u6703\u5f9e {code} \u51fa\u767c\uff01\n"
        f"\u8f38\u5165\u300c\u4fbf\u5b9c\u300d\u8a66\u8a66\u770b \u2708\ufe0f"
    }]


# ─── 文字訊息路由 ─────────────────────────────────────

def handle_text_message(text: str, user_id: str = "") -> list:
    """主要文字訊息路由"""
    text = text.strip()

    # ── 探索最便宜（步驟 1：選月份）──
    # 取得使用者出發地
    origin = _get_user_origin(user_id)

    # ── 出發地設定 ──
    if "出發地" in text or text in ("設定出發地", "出發機場", "改出發地"):
        return handle_set_origin(user_id, text)

    # ── 快速探索（直接秀價格）──
    if text in ("便宜", "最便宜", "探索", "便宜國外探索"):
        return handle_quick_explore(origin)

    # ── 選月份探索 ──
    if text in ("探索最便宜", "便宜探索", "選月份"):
        return _month_picker_flex()

    # ── 探索最便宜（步驟 2：選了月份）──
    if text.startswith("\u63a2\u7d22|"):
        parts = text.split("|")
        if len(parts) >= 2:
            return handle_explore(parts[1], origin)

    # ── 機票比價（步驟 1：提示輸入）──
    if text in ("\u6a5f\u7968\u6bd4\u50f9", "\u6bd4\u50f9", "\u591a\u5e73\u53f0\u6bd4\u50f9"):
        return [{"type": "text", "text":
            "\u2708\ufe0f \u8acb\u544a\u8a34\u6211\u76ee\u7684\u5730\u548c\u65e5\u671f\uff1a\n\n"
            "\U0001f4ac \u7bc4\u4f8b\uff1a\n"
            "\u300c\u6771\u4eac 6/15-6/20\u300d\n"
            "\u300c\u9996\u723e 7\u670810\u523020\u300d\n"
            "\u300c\u66fc\u8c37 8/1~8/7\u300d\n\n"
            "\U0001f4a1 \u652f\u63f4 50+ \u57ce\u5e02\uff0c\u76f4\u63a5\u8f38\u5165\u4e2d\u6587\u57ce\u5e02\u540d\u5373\u53ef"
        }]

    # ── 價格追蹤 ──
    if text.startswith("\u8ffd\u8e64|"):
        return handle_track(user_id, text)

    # ── 取消追蹤 ──
    if text.startswith("\u53d6\u6d88\u8ffd\u8e64"):
        return handle_cancel_track(user_id, text)

    # ── 我的追蹤 ──
    if text in ("\u6211\u7684\u8ffd\u8e64", "\u8ffd\u8e64\u6e05\u55ae", "\u50f9\u683c\u8ffd\u8e64"):
        return handle_my_tracks(user_id)

    # ── 使用教學 / 幫助 ──
    if text in ("\u4f7f\u7528\u6559\u5b78", "\u5e6b\u52a9", "\u8aaa\u660e", "help"):
        return build_help_message()

    # ── 智慧偵測：如果包含城市名 + 日期 → 自動比價 ──
    dest = _parse_destination(text)
    if dest:
        depart, ret = _parse_date_range(text)
        if depart:
            return handle_compare(text, origin)
        else:
            city_name = IATA_TO_NAME.get(dest, dest)
            return [{"type": "text", "text":
                f"\u76ee\u7684\u5730\uff1a{city_name} ({dest}) \u2705\n\n"
                f"\u8acb\u518d\u52a0\u4e0a\u65e5\u671f\uff0c\u4f8b\u5982\uff1a\n"
                f"\u300c{city_name} 6/15-6/20\u300d"
            }]

    # ── 未來功能占位 ──
    coming_soon_keywords = {
        "\u5f48\u6027\u65e5\u671f": "\u5f48\u6027\u65e5\u671f\u641c\u5c0b",
        "\u76f4\u98db": "\u76f4\u98db\u512a\u5148\u63a8\u85a6",
        "\u8f49\u6a5f": "\u8f49\u6a5f\u6700\u7701\u7d44\u5408",
        "\u6a5f\u52a0\u9152": "\u6a5f+\u9152+\u7968\u6253\u5305",
        "\u71b1\u9580\u570b\u5bb6": "\u71b1\u9580\u570b\u5bb6\u5feb\u9078",
        "\u65c5\u884c\u5de5\u5177": "\u65c5\u884c\u5c0f\u5de5\u5177\u7bb1",
    }
    for kw, feature in coming_soon_keywords.items():
        if kw in text:
            return [{"type": "text", "text":
                f"\U0001f6a7 \u300c{feature}\u300d\u5373\u5c07\u4e0a\u7dda\uff0c\u656c\u8acb\u671f\u5f85\uff01\n\n"
                f"\u76ee\u524d\u53ef\u4ee5\u4f7f\u7528\uff1a\n"
                f"\u2022 \U0001f30d \u63a2\u7d22\u6700\u4fbf\u5b9c\n"
                f"\u2022 \u2708\ufe0f \u6a5f\u7968\u6bd4\u50f9\n"
                f"\u2022 \U0001f514 \u50f9\u683c\u8ffd\u8e64"
            }]

    # ── Fallback：不認識的訊息 → 顯示 help ──
    return [{"type": "text", "text":
        "\U0001f914 \u6211\u4e0d\u592a\u78ba\u5b9a\u4f60\u7684\u610f\u601d...\n\n"
        "\u8a66\u8a66\u9019\u6a23\u8f38\u5165\uff1a\n"
        "\u2022 \u300c\u63a2\u7d22\u6700\u4fbf\u5b9c\u300d \u2192 \u770b\u54ea\u88e1\u6700\u4fbf\u5b9c\n"
        "\u2022 \u300c\u6771\u4eac 6/15-6/20\u300d \u2192 \u6a5f\u7968\u6bd4\u50f9\n"
        "\u2022 \u300c\u6211\u7684\u8ffd\u8e64\u300d \u2192 \u67e5\u770b\u8ffd\u8e64\u6e05\u55ae\n\n"
        "\u8f38\u5165\u300c\u4f7f\u7528\u6559\u5b78\u300d\u770b\u5b8c\u6574\u8aaa\u660e \U0001f4d6"
    }]


# ─── 價格檢查（Cron 觸發）────────────────────────────

def check_all_prices():
    """遍歷所有追蹤，檢查價格變化並推播通知"""
    if not UPSTASH_REDIS_URL:
        return {"status": "redis_not_configured"}

    keys = redis_keys("track:*")
    if not keys:
        return {"status": "no_tracks", "count": 0}

    checked = 0
    notified = 0

    for key in keys:
        try:
            data = redis_get(key)
            if not data:
                continue
            info = json.loads(data)

            # 從 key 取得 user_id
            parts = key.split(":")
            if len(parts) < 3:
                continue
            user_id = parts[1]

            # 查最新價格
            flights = None
            if TRAVELPAYOUTS_TOKEN:
                flights = search_flights(
                    info["origin"], info["destination"],
                    info["depart"], info.get("return", "")
                )

            if not flights:
                continue

            cheapest = min(flights, key=lambda x: x.get("price", 99999))
            new_price = cheapest.get("price", 0)
            old_price = info.get("last_price", 0)
            checked += 1

            # 更新價格
            info["last_price"] = new_price
            redis_set(key, json.dumps(info), ttl=86400 * 30)

            # 降價 > 5% → 通知
            if old_price > 0 and new_price < old_price * 0.95:
                savings = old_price - new_price
                dest_name = IATA_TO_NAME.get(info["destination"], info["destination"])
                origin_name = IATA_TO_NAME.get(info["origin"], info["origin"])

                push_message(user_id, [{"type": "text", "text":
                    f"\U0001f514 \u964d\u50f9\u901a\u77e5\uff01\n\n"
                    f"\u2708\ufe0f {origin_name} \u2192 {dest_name}\n"
                    f"\U0001f4c5 {info['depart']}" +
                    (f" ~ {info.get('return', '')}" if info.get("return") else "") + "\n\n"
                    f"\U0001f4b0 NT${old_price:,} \u2192 NT${new_price:,}\n"
                    f"\U0001f389 \u7701 NT${savings:,}\uff01\n\n"
                    f"\u9ede\u6211\u67e5\u770b\u2192 {_tp_booking_url(info['origin'], info['destination'], info['depart'], info.get('return', ''))}"
                }])
                notified += 1

        except Exception as e:
            print(f"[check_prices] Error for {key}: {e}")

    return {"status": "ok", "checked": checked, "notified": notified}


# ─── Vercel Handler ──────────────────────────────────

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """健康檢查 + 價格追蹤 Cron"""
        from urllib.parse import urlparse
        parsed = urlparse(self.path)

        if parsed.path == "/api/check_prices":
            result = check_all_prices()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            # 健康檢查
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "bot": "AbroadUturn"}).encode())

    def do_POST(self):
        """LINE Webhook"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # 驗證簽名
        signature = self.headers.get("X-Line-Signature", "")
        if not verify_signature(body, signature):
            self.send_response(403)
            self.end_headers()
            return

        # 立即回 200（LINE 要求 1 秒內回應）
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

        # 處理事件
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return

        for event in payload.get("events", []):
            reply_token = event.get("replyToken", "")
            user_id = event.get("source", {}).get("userId", "")

            try:
                # Follow 事件（加好友）
                if event.get("type") == "follow":
                    reply_message(reply_token, build_welcome_message())
                    log_usage(user_id, "follow")
                    continue

                # 文字訊息
                if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                    user_text = event["message"]["text"].strip()
                    messages = handle_text_message(user_text, user_id)
                    reply_message(reply_token, messages)

                    # 記錄使用
                    feature = "explore" if "\u63a2\u7d22" in user_text else \
                              "compare" if any(c in user_text for c in ["\u6bd4\u50f9", "\u6a5f\u7968"]) else \
                              "track" if "\u8ffd\u8e64" in user_text else "other"
                    log_usage(user_id, feature)

            except Exception as e:
                print(f"[webhook] Error: {e}")
                reply_message(reply_token, [{"type": "text", "text":
                    "\u7cfb\u7d71\u767c\u751f\u932f\u8aa4\uff0c\u8acb\u7a0d\u5f8c\u518d\u8a66 \U0001f64f"}])
                log_usage(user_id, "error", is_success=False)
