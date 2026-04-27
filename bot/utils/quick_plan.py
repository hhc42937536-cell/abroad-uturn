"""零 API 呼叫的快速完整行程輸出。

組合 itinerary_templates / transport_info / insider_tips / visa_info，
一次回傳最多 5 則 LINE 訊息，不需要等待任何 LLM。
"""
from __future__ import annotations

import datetime
import json
import os

_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
)
_cache: dict = {}


def _load(fname: str) -> dict:
    if fname not in _cache:
        try:
            with open(os.path.join(_DATA_DIR, fname), encoding="utf-8") as f:
                _cache[fname] = json.load(f)
        except Exception:
            _cache[fname] = {}
    return _cache[fname]


def _calc_days(depart: str, ret: str) -> int:
    try:
        d1 = datetime.date.fromisoformat(depart[:10])
        d2 = datetime.date.fromisoformat(ret[:10])
        return max(1, (d2 - d1).days + 1)
    except Exception:
        return 3


# 各城市常見景點關鍵字，用來從原始訊息提取特別需求
_CITY_KW: dict[str, list[str]] = {
    "SEL": ["聖水洞", "弘大", "梨泰院", "東大門", "景福宮", "江南", "狎鷗亭",
            "建大", "明洞", "南大門", "北村", "仁寺洞", "三清洞", "漢南洞",
            "汗蒸幕", "HYBE", "漢江", "益善洞", "廣藏市場", "COEX", "南怡島"],
    "TYO": ["淺草", "秋葉原", "新宿", "澀谷", "原宿", "迪士尼", "teamLab",
            "築地", "台場", "銀座", "上野", "池袋", "中目黑", "蔵前"],
    "OSA": ["道頓堀", "心齋橋", "難波", "黑門市場", "通天閣", "梅田", "天王寺"],
    "BKK": ["考山路", "大皇宮", "暹羅", "ICON Siam", "恰圖恰", "美功鐵道市場"],
    "SIN": ["魚尾獅", "環球影城", "金沙", "牛車水", "小印度", "哈芝巷"],
}
_COMMON_KW = ["按摩", "SPA", "美食之旅", "一日遊", "半日遊", "夜市", "市集",
               "展覽", "美術館", "博物館", "音樂會", "演唱會", "購物"]


def _extract_custom(text: str, dest_code: str) -> str:
    """從原始訊息抽出特別需求關鍵字，逗號串接回傳。"""
    found = [kw for kw in _CITY_KW.get(dest_code, []) + _COMMON_KW if kw in text]
    return "、".join(list(dict.fromkeys(found))[:8])  # 去重、限 8 個


def _day_bubble(day_num: int, date_label: str, theme: str,
                am: str, pm: str, eve: str) -> dict:
    _colors = ["#FF6B35", "#1565C0", "#2E7D32", "#6A1B9A",
               "#00838F", "#E65100", "#283593", "#1B5E20"]
    color = _colors[(day_num - 1) % len(_colors)]

    rows = []
    for icon, label, content in [("🌅", "上午", am), ("☀️", "下午", pm), ("🌙", "晚上", eve)]:
        if content:
            rows.append({
                "type": "box", "layout": "vertical", "spacing": "xs",
                "margin": "sm",
                "contents": [
                    {"type": "text", "text": f"{icon} {label}",
                     "size": "xs", "color": "#888888", "weight": "bold"},
                    {"type": "text", "text": content, "size": "sm",
                     "color": "#333333", "wrap": True},
                ],
            })

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": color, "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"Day {day_num}  {date_label}",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
                {"type": "text", "text": theme,
                 "color": "#FFFFFFCC", "size": "xs", "margin": "xs", "wrap": True},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "none",
            "contents": rows or [
                {"type": "text", "text": "彈性安排，依當天狀況調整",
                 "size": "sm", "color": "#888888"}
            ],
        },
    }


def build_quick_plan(
    dest_code: str,
    city_name: str,
    depart: str,
    ret: str,
    adults: int = 1,
    raw_text: str = "",
) -> list:
    """
    組合靜態資料，0 API 呼叫，回傳最多 5 則 LINE 訊息。

    訊息順序：
      1. Flex Carousel — 每日行程卡
      2. 特別需求 + 必吃清單（text）
      3. 交通攻略（text）
      4. 行前必知 + 在地眉角（text，含 quickReply）
    """
    from bot.constants.cities import IATA_TO_COUNTRY

    tmpl = _load("itinerary_templates.json").get(dest_code) or \
           _load("itinerary_templates.json").get("_default") or {}
    trans = _load("transport_info.json").get(dest_code, {})
    tips = _load("insider_tips.json").get(dest_code, {})
    country_code = IATA_TO_COUNTRY.get(dest_code, "")
    visa = _load("visa_info.json").get(country_code, {})

    days = _calc_days(depart, ret)
    custom_kw = _extract_custom(raw_text, dest_code)

    try:
        depart_dt = datetime.date.fromisoformat(depart[:10])
    except Exception:
        depart_dt = None

    def _dlabel(idx: int) -> str:
        if depart_dt:
            d = depart_dt + datetime.timedelta(days=idx)
            return f"{d.month}/{d.day}"
        return ""

    # ── 訊息 1：每日行程 Carousel ───────────────────────────────
    full_days = tmpl.get("full_days", [])
    arrival = tmpl.get("arrival", {})
    dep_tmpl = tmpl.get("departure", {})
    bubbles = []

    for i in range(days):
        dl = _dlabel(i)
        if i == 0:
            bubbles.append(_day_bubble(
                1, dl, "✈️ 抵達 · Check-in · 初探",
                am="機場入境 → 飯店 Check-in · 辦交通卡",
                pm=arrival.get("pm", "放行李，附近街區散步熟悉環境"),
                eve=arrival.get("eve", "附近覓食，早點休息"),
            ))
        elif i == days - 1:
            bubbles.append(_day_bubble(
                days, dl, "🧳 退房 · 最後採買 · 返程",
                am=dep_tmpl.get("am", "退房前最後採買 · 記得退稅"),
                pm=dep_tmpl.get("pm", "前往機場 · 辦理登機"),
                eve="",
            ))
        else:
            fd = full_days[(i - 1) % len(full_days)] if full_days else {}
            bubbles.append(_day_bubble(
                i + 1, dl,
                fd.get("theme", "自由探索"),
                fd.get("am", ""), fd.get("pm", ""), fd.get("eve", ""),
            ))

    msg1 = {
        "type": "flex",
        "altText": f"✨ {city_name} {days}天行程大綱",
        "contents": {"type": "carousel", "contents": bubbles[:10]},
    }

    # ── 訊息 2：特別需求 + 必吃 ─────────────────────────────────
    parts2 = []
    if custom_kw:
        parts2.append(f"📌 你的特別需求\n{custom_kw}\n（已記錄！想安排在哪天告訴我）")
    must_eat = tmpl.get("must_eat", [])
    if must_eat:
        parts2.append("🍽️ 必吃清單\n" + "\n".join(f"  • {x}" for x in must_eat[:5]))
    msg2 = {"type": "text", "text": "\n\n".join(parts2)} if parts2 else None

    # ── 訊息 3：交通攻略 ─────────────────────────────────────────
    trans_lines = [f"🚇 {city_name}交通攻略\n"]
    cards = trans.get("cards", [])
    if cards:
        c = cards[0]
        trans_lines.append(
            f"交通卡：{c.get('name', '')}（{c.get('deposit', '')}）\n"
            f"  哪裡買：{c.get('where_to_buy', '')}\n"
            f"  可用：{c.get('coverage', '')}"
        )
    metro = trans.get("metro_lines", [])[:4]
    if metro:
        trans_lines.append("主要路線：\n" + "\n".join(f"  {m}" for m in metro))
    for t in trans.get("tips", [])[:3]:
        trans_lines.append(f"  • {t}")
    taxi = trans.get("taxi_app", "")
    if taxi:
        trans_lines.append(f"叫車 APP：{taxi}")
    apps = trans.get("apps", [])[:4]
    if apps:
        trans_lines.append(
            "必裝 APP：" + "  ".join(
                f"{a.get('icon','')} {a.get('name','')}" for a in apps
            )
        )
    msg3 = {"type": "text", "text": "\n".join(trans_lines)} if len(trans_lines) > 1 else None

    # ── 訊息 4：行前必知 + 眉角（含 quickReply）────────────────
    pre_lines = [f"📋 {city_name}行前必知\n"]
    if visa:
        v = "免簽" if not visa.get("visa_required") else "需申請簽證"
        pre_lines.append(
            f"簽證：{v}（最長 {visa.get('stay_limit', '')}）\n"
            f"護照效期：{visa.get('passport_validity', '')}"
            + (f"\n注意：{visa.get('notes', '')}" if visa.get("notes") else "")
        )
    for key, label in [("ticket", "🎫 票務秘訣"), ("crowd", "👥 人潮眉角"),
                       ("hidden", "💎 隱藏景點"), ("money", "💰 省錢撇步")]:
        vals = tips.get(key, [])[:2]
        if vals:
            pre_lines.append(label + "\n" + "\n".join(f"  • {v}" for v in vals))

    msg4 = {
        "type": "text",
        "text": "\n\n".join(pre_lines),
        "quickReply": {"items": [
            {"type": "action", "action": {
                "type": "message", "label": "✈️ 查機票", "text": f"查機票 {city_name}"}},
            {"type": "action", "action": {
                "type": "message", "label": "🏨 查住宿", "text": f"住宿推薦 {city_name}"}},
            {"type": "action", "action": {
                "type": "message", "label": "🔥 最夯玩法", "text": f"最夯玩法 {city_name}"}},
            {"type": "action", "action": {
                "type": "message", "label": "🔄 重新規劃", "text": "重新規劃"}},
        ]},
    }

    return [m for m in [msg1, msg2, msg3, msg4] if m][:5]
