"""日期、目的地、月份解析工具"""

import re

from bot.constants.cities import CITY_CODES


def parse_date_range(text: str) -> tuple:
    """
    解析日期範圍，支援多種格式：
    - "6/15-6/20" -> ("2026-06-15", "2026-06-20")
    - "6/15~6/20" -> ("2026-06-15", "2026-06-20")
    - "2026-06-15 2026-06-20" -> ("2026-06-15", "2026-06-20")
    - "6月15到20" -> ("2026-06-15", "2026-06-20")
    """
    import datetime
    today = datetime.date.today()
    year = today.year

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
    """從文字中解析目的地 IATA 碼"""
    text_lower = text.lower().strip()
    for name, code in CITY_CODES.items():
        if name in text_lower:
            return code
    m = re.search(r"\b([A-Z]{3})\b", text)
    if m:
        return m.group(1)
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
