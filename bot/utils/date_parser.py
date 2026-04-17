"""日期、目的地、月份解析工具"""

import re
import datetime as _dt

from bot.constants.cities import CITY_CODES

# 中文數字 → 阿拉伯數字
_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
           "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
           "十一": 11, "十二": 12}


def _cn_to_int(s: str) -> int | None:
    """把中文數字或阿拉伯數字字串轉成整數"""
    if s.isdigit():
        return int(s)
    return _CN_NUM.get(s)


def _week_monday(year: int, month: int, nth: int) -> _dt.date | None:
    """取得指定年月第 nth 週的週一（nth 從 1 開始）"""
    first = _dt.date(year, month, 1)
    # 第一週的週一
    first_monday = first + _dt.timedelta(days=(7 - first.weekday()) % 7)
    if first_monday.month != month:
        first_monday -= _dt.timedelta(days=7)
    target = first_monday + _dt.timedelta(weeks=nth - 1)
    if target.month != month:
        return None
    return target


def _last_day(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]


def _relative_date_range(text: str) -> tuple | None:
    """
    解析相對日期關鍵字，返回 (depart_str, return_str) 或 None。

    支援：
    - 下週/下周/下禮拜/下個禮拜      → 下週一 ~ 下週日
    - 下下週/下下禮拜                → 兩週後週一 ~ 週日
    - 這週/本週/這禮拜/本禮拜        → 本週一 ~ 本週日
    - 下個月/下月                    → 下個月 1 號 ~ 月底
    - 這個月/本月                    → 今天 ~ 月底
    - X月                           → X 月 1 號 ~ 月底
    - X月第Y週/X月第Y個禮拜         → X 月第 Y 週的週一 ~ 週日
    - 第Y週/第Y個禮拜                → 本月第 Y 週的週一 ~ 週日
    """
    today = _dt.date.today()
    year = today.year

    # ── 下下週 ──────────────────────────────────────────────
    if re.search(r"下下[週周]|下下禮拜|下下個禮拜", text):
        offset = (7 - today.weekday()) % 7 + 7
        monday = today + _dt.timedelta(days=offset if offset > 0 else 7)
        # 確保是兩週後（14天起）
        monday = today + _dt.timedelta(days=(7 - today.weekday()) % 7 + 7)
        if monday == today:
            monday += _dt.timedelta(days=7)
        sunday = monday + _dt.timedelta(days=6)
        return (monday.isoformat(), sunday.isoformat())

    # ── 下週 / 下周 / 下禮拜 ────────────────────────────────
    if re.search(r"下[週周]|下禮拜|下個禮拜", text):
        days_to_monday = (7 - today.weekday()) % 7
        if days_to_monday == 0:
            days_to_monday = 7
        monday = today + _dt.timedelta(days=days_to_monday)
        sunday = monday + _dt.timedelta(days=6)
        return (monday.isoformat(), sunday.isoformat())

    # ── 這週 / 本週 / 本禮拜 ────────────────────────────────
    if re.search(r"[這本][週周]|[這本]禮拜|這個禮拜", text):
        monday = today - _dt.timedelta(days=today.weekday())
        sunday = monday + _dt.timedelta(days=6)
        return (monday.isoformat(), sunday.isoformat())

    # ── 下個月 / 下月 ────────────────────────────────────────
    if re.search(r"下個?月|下月", text):
        m = today.month + 1
        y = year if m <= 12 else year + 1
        m = m if m <= 12 else 1
        last = _last_day(y, m)
        return (f"{y}-{m:02d}-01", f"{y}-{m:02d}-{last:02d}")

    # ── 這個月 / 本月 ────────────────────────────────────────
    if re.search(r"[這本]個?月|本月", text):
        last = _last_day(year, today.month)
        return (today.isoformat(), f"{year}-{today.month:02d}-{last:02d}")

    # ── X月第Y週 / X月第Y個禮拜 ─────────────────────────────
    m = re.search(
        r"(\d{1,2}|[一二三四五六七八九十]{1,3})月"
        r"第(\d{1,2}|[一二三四五六七八九十]{1,3})[個个]?[週周禮拜]",
        text,
    )
    if m:
        mon = _cn_to_int(m.group(1))
        nth = _cn_to_int(m.group(2))
        if mon and nth:
            y = year if mon >= today.month else year + 1
            monday = _week_monday(y, mon, nth)
            if monday:
                sunday = monday + _dt.timedelta(days=6)
                return (monday.isoformat(), sunday.isoformat())

    # ── 第Y週 / 第Y個禮拜（本月）───────────────────────────
    m = re.search(
        r"第(\d{1,2}|[一二三四五六七八九十]{1,3})[個个]?[週周禮拜]",
        text,
    )
    if m:
        nth = _cn_to_int(m.group(1))
        if nth:
            monday = _week_monday(year, today.month, nth)
            if monday:
                sunday = monday + _dt.timedelta(days=6)
                return (monday.isoformat(), sunday.isoformat())

    # ── 純月份：X月 ─────────────────────────────────────────
    m = re.search(r"^(\d{1,2}|[一二三四五六七八九十]{1,3})月$", text.strip())
    if m:
        mon = _cn_to_int(m.group(1))
        if mon:
            y = year if mon >= today.month else year + 1
            last = _last_day(y, mon)
            return (f"{y}-{mon:02d}-01", f"{y}-{mon:02d}-{last:02d}")

    return None


def parse_date_range(text: str) -> tuple:
    """
    解析日期範圍，支援多種格式：
    - "6/15-6/20" -> ("2026-06-15", "2026-06-20")
    - "6/15~6/20" -> ("2026-06-15", "2026-06-20")
    - "2026-06-15 2026-06-20" -> ("2026-06-15", "2026-06-20")
    - "6月15到20" -> ("2026-06-15", "2026-06-20")
    - "下週" -> (next Monday, next Sunday)
    - "下個月" -> (1st, last day of next month)
    - "6月第2週" -> (2nd Monday of June, that Sunday)
    """
    today = _dt.date.today()
    year = today.year

    # 相對日期優先解析
    rel = _relative_date_range(text)
    if rel:
        return rel

    m = re.search(r"(\d{1,2})/(\d{1,2})\s*[-~]\s*(\d{1,2})/(\d{1,2})", text)
    if m:
        m1, d1, m2, d2 = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        y1 = year if m1 >= today.month else year + 1
        y2 = year if m2 >= today.month else year + 1
        return (f"{y1}-{m1:02d}-{d1:02d}", f"{y2}-{m2:02d}-{d2:02d}")

    m = re.search(r"(\d{4}-\d{2}-\d{2})\s*[-~到]\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        return (m.group(1), m.group(2))

    m = re.search(r"(\d{1,2})月(\d{1,2})\s*[-~到]\s*(\d{1,2})", text)
    if m:
        mon, d1, d2 = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = year if mon >= today.month else year + 1
        return (f"{y}-{mon:02d}-{d1:02d}", f"{y}-{mon:02d}-{d2:02d}")

    m = re.search(r"(\d{1,2})/(\d{1,2})", text)
    if m:
        mon, day = int(m.group(1)), int(m.group(2))
        y = year if mon >= today.month else year + 1
        return (f"{y}-{mon:02d}-{day:02d}", "")

    return ("", "")


def parse_destination(text: str) -> str:
    """從文字中解析目的地 IATA 碼；關鍵字失敗時用 LLM 補救。"""
    import os
    text_lower = text.lower().strip()
    for name, code in CITY_CODES.items():
        if name in text_lower:
            return code
    m = re.search(r"\b([A-Z]{3})\b", text)
    if m:
        return m.group(1)

    # 關鍵字全部失敗 → 用 LLM 推斷（大谷翔平、極光、名人等）
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{"role": "user", "content":
                f"用戶說：「{text}」\n"
                "請判斷他最可能想去的城市，只回傳英文城市名（如 Tokyo、Los Angeles、Seoul），"
                "完全無法判斷才回傳 UNKNOWN。不要其他文字。"}],
        )
        city_en = msg.content[0].text.strip()
        if city_en.upper() == "UNKNOWN":
            return ""
        # 對照英文城市名
        _EN_MAP = {
            "tokyo": "TYO", "osaka": "OSA", "seoul": "SEL", "busan": "PUS",
            "bangkok": "BKK", "singapore": "SIN", "kuala lumpur": "KUL",
            "hong kong": "HKG", "taipei": "TPE",
            "los angeles": "LAX", "new york": "NYC", "san francisco": "SFO",
            "london": "LON", "paris": "PAR", "rome": "ROM", "milan": "MIL",
            "sydney": "SYD", "melbourne": "MEL", "dubai": "DXB",
            "bali": "DPS", "manila": "MNL", "ho chi minh": "SGN",
            "hanoi": "HAN", "jakarta": "JKT", "fukuoka": "FUK",
            "sapporo": "CTS", "okinawa": "OKA",
            "reykjavik": "REK", "reykjavík": "REK",
            "tromsø": "TOS", "tromso": "TOS",
            "helsinki": "HEL", "rovaniemi": "RVN",
            "toronto": "YTO", "vancouver": "YVR",
            "vienna": "VIE", "prague": "PRG", "zurich": "ZRH",
            "istanbul": "IST", "barcelona": "BCN", "amsterdam": "AMS",
        }
        print(f"[dest_llm] text={repr(text[:40])} → {city_en}")
        return _EN_MAP.get(city_en.lower(), "")
    except Exception as e:
        print(f"[dest_llm] error: {e}")
        return ""


def parse_month(text: str) -> str:
    """從文字解析月份，返回 YYYY-MM 格式"""
    import datetime
    today = datetime.date.today()
    year = today.year
    m = re.search(r"(\d{4})[-/](\d{1,2})", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    m = re.search(r"(\d{1,2})月", text)
    if m:
        mon = int(m.group(1))
        y = year if mon >= today.month else year + 1
        return f"{y}-{mon:02d}"
    return ""


def duration_str(minutes: int) -> str:
    if minutes <= 0:
        return ""
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"
