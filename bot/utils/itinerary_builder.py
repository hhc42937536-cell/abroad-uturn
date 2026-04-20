"""行程大綱生成器（LLM 優先 + 靜態範本 fallback + 季節性標籤）

根據目的地 + 天數，自動組合 Day 1 ~ Day N 的行程大綱，
輸出為 LINE Flex Bubble（可放進 Carousel 或單獨回覆）。
"""

import json
import os
import datetime

_SEASONAL_EVENTS = {
    "JP": [
        ((3, 4),   "🌸 櫻花季", "賞花推薦：上野公園・目黒川・圓山公園"),
        ((11, 12), "🍁 楓葉季", "賞楓推薦：嵐山・日光・高尾山"),
        ((7, 8),   "🎆 夏祭",   "祭典推薦：淺草三社祭・住吉大社夏祭"),
        ((12, 1),  "❄️ 雪景",   "賞雪推薦：北海道・白川鄉合掌村"),
    ],
    "KR": [
        ((3, 4),   "🌸 櫻花季", "賞花推薦：鎮海軍港節・慶州"),
        ((10, 11), "🍁 楓葉季", "賞楓推薦：雪嶽山・北漢山"),
        ((1, 2),   "⛷️ 滑雪季", "滑雪推薦：洪川・龍平・鳳凰城"),
    ],
    "TH": [
        ((4, 4),   "💦 潑水節",     "宋干節潑水節（4月中旬），全泰國最熱鬧"),
        ((11, 11), "🏮 水燈節",     "萬人放水燈・清邁最美"),
        ((11, 2),  "☀️ 涼季旺季",   "溫度宜人，最適合戶外活動"),
    ],
    "JP_OKA": [
        ((5, 9),   "🌺 海灘旺季",   "水溫最佳，珊瑚礁浮潛・海水浴推薦"),
    ],
    "ID": [
        ((7, 9),   "☀️ 乾季旺季",   "巴里島最適合海灘活動的季節"),
        ((6, 7),   "🎭 巴里藝術節", "傳統舞蹈・手工藝展覽"),
    ],
    "VN": [
        ((2, 4),   "🌸 春季旅遊",   "天氣涼爽，節慶氛圍濃厚"),
        ((9, 11),  "🏖️ 中越旺季",   "會安・峴港天氣最好"),
    ],
    "SG": [
        ((12, 2),  "🎉 聖誕跨年",   "烏節路燈飾・跨年倒數活動"),
        ((6, 9),   "✈️ 旅遊旺季",   "晴天為主，適合戶外景點"),
    ],
}

_IATA_COUNTRY_SEASON = {
    "NRT": "JP", "HND": "JP", "TYO": "JP", "KIX": "JP", "OSA": "JP",
    "FUK": "JP", "NGO": "JP", "CTS": "JP",
    "OKA": "JP_OKA",
    "ICN": "KR", "SEL": "KR", "GMP": "KR", "PUS": "KR",
    "BKK": "TH", "DMK": "TH",
    "DPS": "ID",
    "SGN": "VN", "HAN": "VN",
    "SIN": "SG",
}


def _get_seasonal_tag(dest_code: str, travel_month: int):
    """返回 (tag_str, activity_str) 或 None"""
    country = _IATA_COUNTRY_SEASON.get(dest_code)
    if not country:
        return None
    for (start_m, end_m), tag, activity in _SEASONAL_EVENTS.get(country, []):
        if start_m <= end_m:
            hit = start_m <= travel_month <= end_m
        else:
            hit = travel_month >= start_m or travel_month <= end_m
        if hit:
            return tag, activity
    return None

_data_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data"
)
_cache = {}

# IATA → 範本 key 對照（多個 IATA 可對應同一城市）
_IATA_MAP = {
    # 日本
    "TYO": "TYO", "NRT": "TYO", "HND": "TYO",
    "OSA": "OSA", "KIX": "OSA", "ITM": "OSA",
    "OKA": "OKA",
    "FUK": "OSA",   # 福岡先用大阪模板（可之後補充）
    "NGO": "TYO",   # 名古屋先用東京模板
    "SPK": "TYO",   # 札幌先用東京模板
    # 韓國
    "SEL": "SEL", "ICN": "SEL", "GMP": "SEL",
    "PUS": "PUS",
    # 東南亞
    "BKK": "BKK", "DMK": "BKK",
    "SIN": "SIN",
    "SGN": "SGN", "HAN": "SGN",
    # 香港
    "HKG": "HKG",
    # 沖繩
}


def _load_templates() -> dict:
    if "itinerary" in _cache:
        return _cache["itinerary"]
    try:
        path = os.path.join(_data_dir, "itinerary_templates.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["itinerary"] = data
        return data
    except Exception as e:
        print(f"[itinerary] Load error: {e}")
        return {}


def _get_template(dest_code: str) -> dict:
    templates = _load_templates()
    key = _IATA_MAP.get(dest_code, dest_code)
    return templates.get(key) or templates.get("_default") or {}


def _calc_days(depart: str, ret: str) -> int:
    try:
        d1 = datetime.date.fromisoformat(depart[:10])
        d2 = datetime.date.fromisoformat(ret[:10])
        return max(1, (d2 - d1).days + 1)
    except Exception:
        return 3


def _day_bubble(day_num: int, label: str, plan: dict, depart_date: str = "") -> dict:
    """單天行程 Flex Bubble"""
    # 計算日期顯示
    date_label = ""
    if depart_date:
        try:
            d = datetime.date.fromisoformat(depart_date[:10])
            actual = d + datetime.timedelta(days=day_num - 1)
            date_label = f"  {actual.month}/{actual.day}"
        except Exception:
            pass

    header_color = "#FF6B35" if day_num == 1 else (
        "#1565C0" if day_num % 2 == 0 else "#2E7D32"
    )

    rows = []
    if plan.get("am"):
        rows.append(_time_row("🌅 上午", plan["am"]))
    if plan.get("pm"):
        rows.append(_time_row("☀️ 下午", plan["pm"]))
    if plan.get("eve"):
        rows.append(_time_row("🌙 晚上", plan["eve"]))

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_color, "paddingAll": "12px",
            "contents": [
                {"type": "text",
                 "text": f"Day {day_num}{date_label}",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
                {"type": "text",
                 "text": label,
                 "color": "#FFFFFFCC", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "12px",
            "contents": rows or [
                {"type": "text", "text": "彈性安排，依當天狀況調整",
                 "size": "sm", "color": "#888888"}
            ],
        },
    }


def _time_row(time_label: str, content: str) -> dict:
    return {
        "type": "box", "layout": "vertical", "margin": "sm",
        "contents": [
            {"type": "text", "text": time_label,
             "size": "xs", "color": "#888888", "weight": "bold"},
            {"type": "text", "text": content,
             "size": "sm", "color": "#333333", "wrap": True, "margin": "xs"},
        ],
    }


def _llm_day_plans(city_name: str, days: int, seasonal_tag: str = "",
                   budget: str = "", adults: int = 1,
                   custom_requests: str = "",
                   dest_code: str = "") -> list | None:
    """
    呼叫 Claude Haiku 生成每日行程 JSON。
    回傳 list[{"theme":..., "am":..., "pm":..., "eve":...}] 或 None（失敗時）。
    結果以 Redis 快取 24 小時，避免重複呼叫。
    """
    try:
        import anthropic
        from bot.services.redis_store import redis_get, redis_set
    except ImportError:
        return None

    cache_key = f"llm_itinerary:{city_name}:{days}:{budget}:{custom_requests[:20]}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    season_hint = f"（出發時正值{seasonal_tag}）" if seasonal_tag else ""
    budget_hint = f"預算約 {budget}" if budget else ""
    adults_hint = f"{adults}人同行" if adults > 1 else "獨自旅行"
    custom_hint = f"\n特別需求：{custom_requests}" if custom_requests else ""

    # 注入在地眉角（票務/人潮/交通/隱藏景點）
    insider_block = ""
    if dest_code:
        try:
            from bot.services.travel_data import get_insider_tips
            tips = get_insider_tips(dest_code)
            if tips:
                parts = []
                if tips.get("ticket"):
                    parts.append("【票務時機】" + "；".join(tips["ticket"][:3]))
                if tips.get("crowd"):
                    parts.append("【人潮眉角】" + "；".join(tips["crowd"][:3]))
                if tips.get("transport"):
                    parts.append("【交通秘技】" + "；".join(tips["transport"][:2]))
                if tips.get("hidden"):
                    parts.append("【隱藏景點】" + "；".join(tips["hidden"][:2]))
                if parts:
                    insider_block = (
                        "\n\n以下是台灣旅客專屬的在地眉角，請優先融入行程建議中（這些資訊一般旅遊網站查不到）：\n"
                        + "\n".join(parts)
                    )
        except Exception:
            pass

    prompt = (
        f"請為台灣旅客規劃{city_name} {days}天旅遊行程{season_hint}，{adults_hint}，{budget_hint}。{custom_hint}{insider_block}\n\n"
        f"只需回傳第 2 天到第 {days-1} 天（不含抵達/返台日）的中間天，共 {max(days-2,1)} 天。\n"
        f"回傳 JSON array，每個元素格式：\n"
        f'  {{"theme":"主題","am":"上午行程（1~2句，含具體時間/秘訣）","pm":"下午行程","eve":"晚上行程"}}\n'
        f"只回傳 JSON array，不要其他文字。請融入在地眉角讓建議比一般 Google 搜尋更有價值。"
    )

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        client = anthropic.Anthropic(api_key=api_key, timeout=8.0)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # 擷取 JSON array（防止 LLM 回傳多餘文字）
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            return None
        plans = json.loads(raw[start:end])
        if isinstance(plans, list) and plans:
            redis_set(cache_key, json.dumps(plans, ensure_ascii=False), ttl=60 * 60 * 24)
            return plans
    except Exception as e:
        print(f"[itinerary] LLM error: {e}")
    return None


def build_itinerary_flex(dest_code: str, depart_date: str, return_date: str,
                         city_name: str = "", custom_requests: str = "",
                         budget: str = "", adults: int = 1) -> list:
    """
    生成行程大綱 Flex Carousel（1 則訊息）
    優先使用 Claude Haiku 生成個人化行程，失敗時 fallback 靜態範本。
    回傳 list[dict]，可直接 append 到 messages。
    """
    tmpl = _get_template(dest_code)
    days = _calc_days(depart_date, return_date)
    display_city = city_name or (tmpl.get("city_name", dest_code) if tmpl else dest_code)
    must_eat = tmpl.get("must_eat", []) if tmpl else []
    full_day_templates = tmpl.get("full_days", []) if tmpl else []

    # 取出行程月份，用於季節偵測
    try:
        travel_month = datetime.date.fromisoformat(depart_date[:10]).month
    except Exception:
        travel_month = datetime.date.today().month
    seasonal = _get_seasonal_tag(dest_code, travel_month)
    seasonal_tag = seasonal[0] if seasonal else ""

    # 嘗試 LLM 生成中間天行程（Day 2 ~ Day N-1）
    llm_plans = None
    if days >= 3:
        llm_plans = _llm_day_plans(
            display_city, days, seasonal_tag, budget, adults, custom_requests,
            dest_code=dest_code
        )

    bubbles = []
    llm_idx = 0

    for day_num in range(1, days + 1):
        if day_num == 1:
            plan = tmpl.get("arrival", {}) if tmpl else {}
            label = f"抵達 {display_city}"
        elif day_num == days:
            plan = tmpl.get("departure", {}) if tmpl else {}
            label = "歸途 · 返台"
        else:
            if llm_plans and llm_idx < len(llm_plans):
                plan = llm_plans[llm_idx]
                llm_idx += 1
                label = plan.get("theme", "深度探索")
            else:
                idx = (day_num - 2) % max(len(full_day_templates), 1)
                plan = full_day_templates[idx] if full_day_templates else {}
                label = plan.get("theme", "深度探索")

        bubbles.append(_day_bubble(day_num, label, plan, depart_date))

    # 季節活動 bubble（有季節事件才顯示）
    if seasonal:
        tag, activity = seasonal
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E65100", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": tag,
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "你出發的時間剛好遇到！",
                     "color": "#FFFFFF99", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "12px", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": activity,
                     "size": "sm", "color": "#333333", "wrap": True},
                    {"type": "text",
                     "text": "⚡ 建議提前預約熱門景點或場地",
                     "size": "xs", "color": "#888888", "margin": "sm", "wrap": True},
                ],
            },
        })

    # 必吃清單 bubble
    if must_eat:
        eat_lines = [{"type": "text", "text": f"• {item}",
                      "size": "sm", "color": "#555555", "wrap": True}
                     for item in must_eat[:6]]
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E63", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": f"🍜 {display_city} 必吃清單",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "出發前先記起來！",
                     "color": "#FFFFFF99", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "xs", "paddingAll": "12px",
                "contents": eat_lines,
            },
        })

    if not bubbles:
        return []

    seasonal_hint = f"  {seasonal[0]}" if seasonal else ""
    ai_hint = "  ✨ AI 個人化" if llm_plans else ""
    return [
        {"type": "text",
         "text": f"📅 {display_city} {days}天行程大綱{seasonal_hint}{ai_hint}\n← 左右滑動看每天安排"},
        {
            "type": "flex",
            "altText": f"{display_city} {days}天行程大綱",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]
