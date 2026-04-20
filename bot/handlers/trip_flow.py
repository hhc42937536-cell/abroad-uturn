"""8 步引導式旅程規劃流程控制器（狀態機核心）

Phase 2 會完整實作每個步驟。目前先建立骨架。
"""

from bot.session.manager import (
    get_session, get_step, set_session, update_session,
    clear_session, start_session,
)
from bot.handlers.settings import get_user_origin


def start(user_id: str) -> list:
    """步驟 0：進入規劃模式"""
    origin = get_user_origin(user_id)
    start_session(user_id, origin)

    return [
        {
            "type": "flex",
            "altText": "\u2728 \u958b\u59cb\u898f\u5283\u65c5\u7a0b",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "20px",
                    "contents": [
                        {"type": "text", "text": "\u2728 \u51fa\u570b\u512a\u8f49 - \u5b8c\u6574\u65c5\u7a0b\u898f\u5283",
                         "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": "\u6211\u6703\u50cf\u4f60\u7684\u5c08\u5c6c\u65c5\u884c\u9867\u554f\uff0c\u5e36\u4f60\u5f9e\u982d\u5230\u5c3e\u898f\u5283\u4e00\u6b21\u65c5\u884c\u3002",
                         "color": "#FFE0CC", "size": "sm", "margin": "md", "wrap": True},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "md", "paddingAll": "20px",
                    "contents": [
                        {"type": "text", "text": "\U0001f4cb \u898f\u5283\u6d41\u7a0b", "weight": "bold", "size": "md"},
                        {"type": "separator"},
                        {"type": "text", "text":
                            "\u2460 \u9078\u76ee\u7684\u5730\n"
                            "\u2461 \u9078\u65e5\u671f\n"
                            "\u2462 \u4eba\u6578\u8207\u9810\u7b97\n"
                            "\u2463 \u6a5f\u7968\u63a8\u85a6\n"
                            "\u2464 \u4f4f\u5bbf\u63a8\u85a6\n"
                            "\u2465 \u884c\u7a0b\u5927\u7db1\n"
                            "\u2466 \u884c\u524d\u9808\u77e5\n"
                            "\u2467 \u5b8c\u6574\u8a08\u756b\u66f8",
                         "size": "sm", "color": "#555555", "wrap": True},
                        {"type": "text", "text": "\u6574\u500b\u904e\u7a0b\u5927\u7d04 5-8 \u5206\u9418\u5373\u53ef\u5b8c\u6210\u3002",
                         "size": "xs", "color": "#999999", "margin": "md"},
                    ],
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#FF6B35",
                         "action": {"type": "postback", "label": "\U0001f680 \u958b\u59cb\u898f\u5283\uff01",
                                    "data": "trip_step=1", "displayText": "\u958b\u59cb\u898f\u5283\uff01"}},
                    ],
                },
            },
        }
    ]


def start_with_flight(user_id: str, dest_code: str, depart: str, ret: str) -> list:
    """從機票卡片直接進規劃：跳過目的地+日期，直接到步驟3（人數）"""
    from bot.constants.cities import IATA_TO_NAME, IATA_TO_COUNTRY
    origin = get_user_origin(user_id)
    start_session(user_id, origin)
    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    country_code = IATA_TO_COUNTRY.get(dest_code, "")
    update_session(user_id, {
        "destination_code": dest_code,
        "destination_name": city_name,
        "country_code": country_code,
        "flexibility": "specific",
        "depart_date": depart,
        "return_date": ret,
        "flight_confirmed": True,  # 已從機票卡片選定，跳過 step 4
    }, step=3)
    return [{
        "type": "text",
        "text": f"✅ 目的地：{city_name}\n✅ 日期：{depart[5:].replace('-','/')} → {ret[5:].replace('-','/') if ret else '單程'}\n\n直接跳到步驟 3，幾個人出發？",
    }] + _prompt_travelers(user_id)


# ── 情境化提示：(IATA碼, 風格關鍵字) → 顧問式追問 ──────────────────────────
_DEST_STYLE_TIPS: dict[tuple[str, str], str] = {
    ("CTS", "滑雪"): "Niseko 適合中高手，富良野適合初學者，你是哪種程度？",
    ("TYO", "購物"): "新宿、原宿、銀座各有特色，你偏哪一類？",
    ("OSA", "美食"): "大阪「天下の台所」，道頓堀、黑門市場都是必訪！",
    ("SEL", "追星"): "SM、YG、HYBE 聖地都在首爾，你追哪個組合？",
    ("BKK", "美食"): "曼谷街頭美食和米其林餐廳都超值，你傾向哪種？",
    ("DPS", "自然"): "峇里島梯田、火山、海灘，你最想體驗哪個？",
    ("SIN", "美食"): "獅城美食文化超多元，老巴剎夜市、麥士威熟食中心你知道嗎？",
    ("HKG", "購物"): "銅鑼灣、旺角、尖沙咀各有風格，你想逛哪一帶？",
    ("NRT", "滑雪"): "關東滑雪推薦草津、尾瀨岩鞍，你是初學還是進階？",
}

_STYLE_DETECT: list[tuple[str, str]] = [
    ("滑雪", "滑雪"), ("雪場", "滑雪"),
    ("購物", "購物"), ("掃貨", "購物"), ("逛街", "購物"),
    ("美食", "美食"), ("必吃", "美食"), ("吃吃喝喝", "美食"),
    ("追星", "追星"), ("演唱會", "追星"), ("見面會", "追星"),
    ("自然", "自然"), ("健行", "自然"), ("爬山", "自然"),
    ("親子", "親子"), ("小孩", "親子"),
    ("蜜月", "蜜月"), ("情侶", "蜜月"),
]


def _llm_tip(dest_code: str, city_name: str, style: str) -> str:
    """用 Haiku 生成情境化追問，結果存 Redis 7天。timeout=3s，失敗回空字串。"""
    import os
    try:
        from bot.services.redis_store import redis_get, redis_set
        cache_key = f"smart_tip:{dest_code}:{style}"
        cached = redis_get(cache_key)
        if cached:
            return cached

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return ""
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, timeout=3.0)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content":
                f"你是台灣旅遊達人。用戶想去{city_name}體驗「{style}」。"
                f"用一句繁體中文問他一個能幫助規劃的關鍵問題，親切口語，不超過30字，不要開頭問候。"}],
        )
        tip = msg.content[0].text.strip()
        redis_set(cache_key, tip, ttl=7 * 86400)
        return tip
    except Exception as e:
        print(f"[smart_tip] {e}")
        return ""


def _smart_greeting(dest_code: str, city_name: str, flag: str,
                    text: str, hints: dict) -> str:
    """生成情境化開場白，聽起來像旅行顧問而非制式系統。"""
    style = next((st for kw, st in _STYLE_DETECT if kw in text), "")

    depart = hints.get("depart_date", "")
    month_hint = ""
    if depart and len(depart) >= 7:
        try:
            month_hint = f"{int(depart[5:7])}月"
        except Exception:
            pass

    # 1. 硬寫的高品質 tip（常見組合，零延遲）
    tip = _DEST_STYLE_TIPS.get((dest_code, style))
    if not tip and style:
        # 2. LLM 動態生成（首次 3s，之後走 Redis 快取）
        tip = _llm_tip(dest_code, city_name, style)

    if tip:
        return f"{flag} {city_name}{month_hint}{style}行程！{tip}"
    if style:
        return f"{flag} {city_name}{month_hint}，{style}好選擇！"
    return f"{flag} {city_name}{month_hint}，好選擇！"


def start_smart(user_id: str, text: str) -> list:
    """智慧快速啟動：解析文字中所有已知資訊，跳過已知步驟，情境化問缺口。"""
    from bot.utils.date_parser import parse_destination_keyword, parse_destination
    from bot.constants.cities import IATA_TO_NAME, IATA_TO_COUNTRY, CITY_FLAG

    origin = get_user_origin(user_id)
    start_session(user_id, origin)
    hints = _parse_hints_from_text(text)

    _HINT_KEYS = {"budget", "adults", "depart_date", "return_date",
                  "flexibility", "custom_requests", "event_date", "is_event_trip"}

    dest_code = parse_destination_keyword(text)
    if not dest_code:
        # LLM 猜測失敗也走 step 1，但帶上已解析的 hints
        llm_code = parse_destination(text)
        if hints:
            update_session(user_id, {k: v for k, v in hints.items() if k in _HINT_KEYS})
        if llm_code:
            hints["_llm_dest"] = llm_code
        return _step1_destination(user_id, text)

    city_name = IATA_TO_NAME.get(dest_code, dest_code)
    country_code = IATA_TO_COUNTRY.get(dest_code, "")
    flag = CITY_FLAG.get(dest_code, "")

    session_data = {
        "destination_code": dest_code,
        "destination_name": city_name,
        "country_code": country_code,
        **{k: v for k, v in hints.items() if k in _HINT_KEYS},
    }

    has_date = bool(hints.get("depart_date"))
    has_travelers = "adults" in hints

    if has_date and has_travelers:
        update_session(user_id, session_data, step=4)
        greeting = _smart_greeting(dest_code, city_name, flag, text, hints)
        return [{"type": "text", "text": f"{greeting}\n\n✅ 目的地、日期、人數都記下了，幫你找機票！"}] + _prompt_flights(user_id)

    # 資訊不齊 → 進 LLM 對話蒐集模式
    update_session(user_id, session_data, step=1)
    greeting = _smart_greeting(dest_code, city_name, flag, text, hints)
    return _llm_gather(user_id, text, greeting=greeting)


def start_with_destination(user_id: str, text: str) -> list:
    """從智慧偵測直接啟動規劃，跳過歡迎頁，直接到步驟 1（確認目的地）"""
    origin = get_user_origin(user_id)
    start_session(user_id, origin)
    return _step1_destination(user_id, text)


_INTENT_LABELS: dict[str, str] = {
    "compare":   "查機票比價",
    "explore":   "探索便宜目的地",
    "visa":      "查簽證資訊",
    "transport": "查交通攻略",
    "hotel":     "查住宿推薦",
    "souvenir":  "查最夯玩法 / 伴手禮",
    "idol":      "規劃追星行程",
    "pre_trip":  "查行前必知",
    "tracking":  "管理價格追蹤",
    "help":      "使用說明",
}

# 這些步驟使用者輸入的是自由文字，不做計分攔截
_FREE_INPUT_STEPS = {1, 2, 3, 6}

# 計分達到此門檻才視為「明確的其他意圖」
_INTENT_INTERCEPT_SCORE = 4


def _gather_fallback(user_id: str, text: str, session: dict) -> list:
    """LLM 失敗時降級：看缺什麼就用舊有制式卡片補。"""
    if not session.get("destination_code"):
        return _step1_destination(user_id, text)
    if not session.get("depart_date"):
        return _step2_dates(user_id, text)
    if not session.get("adults"):
        update_session(user_id, {"adults": 1}, step=4)
    else:
        update_session(user_id, {}, step=4)
    return _prompt_flights(user_id)


def _llm_gather(user_id: str, text: str, greeting: str = "") -> list:
    """
    LLM 驅動的對話式資訊蒐集（取代 Step 1-3 制式卡片）。
    每輪萃取新資訊、更新 session，缺什麼問什麼；
    目的地 + 日期齊全後自動觸發 Step 4。
    """
    import json, os
    session = get_session(user_id) or {}

    # 整理已知欄位給 LLM
    known: dict = {}
    for k, label in [("destination_name", "destination"), ("depart_date", "depart_date"),
                     ("return_date", "return_date"), ("adults", "adults"),
                     ("budget", "budget"), ("custom_requests", "custom_requests")]:
        if session.get(k):
            known[label] = session[k]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _gather_fallback(user_id, text, session)

    prompt = (
        f"你是台灣旅遊顧問。\n"
        f"已知資訊：{json.dumps(known, ensure_ascii=False)}\n"
        f"用戶說：「{text}」\n\n"
        f"請：\n"
        f"1. 從用戶訊息萃取新資訊（只萃取明確說的）：\n"
        f"   destination=城市中文名、depart_date=YYYY-MM或YYYY-MM-DD、"
        f"return_date=YYYY-MM-DD、adults=整數、budget=台幣整數、custom_requests=偏好文字\n"
        f"2. 合併已知+新萃取，若同時具備「目的地」和「出發日期/月份」→ ready:true\n"
        f"3. ready:false 時，用一句口語繁體中文問最重要的缺口，15-25 字，親切自然\n\n"
        "只回傳 JSON，不要其他文字：\n"
        '{"extracted":{"destination":"","depart_date":"","return_date":"",'
        '"adults":0,"budget":0,"custom_requests":""},"next_question":"","ready":false}'
    )

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, timeout=5.0)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=220,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        s, e = raw.find("{"), raw.rfind("}") + 1
        if s == -1:
            raise ValueError("no JSON")
        result = json.loads(raw[s:e])
    except Exception as exc:
        print(f"[llm_gather] {exc}")
        return _gather_fallback(user_id, text, session)

    extracted = result.get("extracted", {})
    ready = result.get("ready", False)
    next_q = result.get("next_question", "")

    # 更新 session
    updates: dict = {}
    if extracted.get("destination") and not session.get("destination_code"):
        from bot.utils.date_parser import parse_destination_keyword, parse_destination
        from bot.constants.cities import IATA_TO_NAME, IATA_TO_COUNTRY
        code = (parse_destination_keyword(extracted["destination"])
                or parse_destination(extracted["destination"]))
        if code:
            updates["destination_code"] = code
            updates["destination_name"] = IATA_TO_NAME.get(code, extracted["destination"])
            updates["country_code"] = IATA_TO_COUNTRY.get(code, "")
        else:
            updates["destination_name"] = extracted["destination"]

    if extracted.get("depart_date"):
        dv = extracted["depart_date"]
        updates["depart_date"] = dv
        updates["flexibility"] = "month" if len(dv) == 7 else "specific"
    if extracted.get("return_date"):
        updates["return_date"] = extracted["return_date"]
    if extracted.get("adults", 0) > 0:
        updates["adults"] = extracted["adults"]
    if extracted.get("budget", 0) > 0:
        updates["budget"] = extracted["budget"]
    if extracted.get("custom_requests"):
        exist = session.get("custom_requests", "")
        nc = extracted["custom_requests"]
        updates["custom_requests"] = f"{exist}；{nc}" if exist else nc

    # 真正 ready 的條件：dest_code + depart_date 都存在
    has_dest = updates.get("destination_code") or session.get("destination_code")
    has_date = updates.get("depart_date") or session.get("depart_date")

    if ready and has_dest and has_date:
        if not updates.get("adults") and not session.get("adults"):
            updates["adults"] = 1
        update_session(user_id, updates, step=4)
        confirm = "✅ 資訊齊全，幫你搜尋機票！"
        if greeting:
            return [{"type": "text", "text": f"{greeting}\n\n{confirm}"}] + _prompt_flights(user_id)
        return [{"type": "text", "text": confirm}] + _prompt_flights(user_id)

    # 還有缺口，繼續問
    update_session(user_id, updates, step=1)
    reply = next_q or "請告訴我目的地、大概幾月去？"
    if greeting:
        reply = f"{greeting}\n\n{reply}"
    return [{"type": "text", "text": reply}]


def handle_step(user_id: str, text: str, step: int) -> list:
    """根據目前步驟處理使用者輸入"""
    # ── 全域跳脫：計分偵測到明確的非規劃意圖 ──
    if step not in _FREE_INPUT_STEPS:
        from bot.utils.intent import classify_intent_scored
        intent, score = classify_intent_scored(text)
        if score >= _INTENT_INTERCEPT_SCORE and intent not in ("plan_trip", "unknown"):
            label = _INTENT_LABELS.get(intent, intent)
            return [{
                "type": "text",
                "text": f"你目前有一個規劃進行到第 {step}/8 步喔！\n\n"
                        f"偵測到你可能想「{label}」\n\n"
                        "• 輸入「繼續規劃」回到剛才的步驟\n"
                        "• 輸入「取消規劃」結束規劃、查詢其他功能",
                "quickReply": {"items": [
                    {"type": "action", "action": {"type": "message",
                        "label": "繼續規劃", "text": "繼續規劃"}},
                    {"type": "action", "action": {"type": "message",
                        "label": "取消規劃", "text": "取消規劃"}},
                ]},
            }]

    # Steps 1-3 全部走 LLM 對話蒐集，降級時再走個別制式 handler
    if step in (1, 2, 3):
        return _llm_gather(user_id, text)

    handlers = {
        4: _step4_flights,
        5: _step5_hotels,
        6: _step6_itinerary,
        7: _step7_travel_info,
        8: _step8_summary,
    }

    handler = handlers.get(step)
    if handler:
        return handler(user_id, text)

    return [{"type": "text", "text": "請繼續輸入資料，或輸入「取消規劃」中止。"}]


def handle_postback(user_id: str, data: str) -> list:
    """處理 postback 事件（步驟導航按鈕）"""
    import urllib.parse
    params = dict(urllib.parse.parse_qsl(data))

    if "trip_step" in params:
        target_step = int(params["trip_step"])
        session = get_session(user_id)
        if not session:
            return start(user_id)

        from bot.session.manager import set_session
        set_session(user_id, session, step=target_step)
        # 進入步驟 8（計畫書）時，先插入行程大綱再顯示計畫書
        if target_step == 8:
            from bot.utils.itinerary_builder import build_itinerary_flex
            dest = session.get("destination_code", "")
            city = session.get("destination_name", "")
            depart = session.get("depart_date", "")
            ret = session.get("return_date", "")
            custom = session.get("custom_requests", "")
            budget_num = session.get("budget", 0)
            budget = f"NT${budget_num//10000}萬" if budget_num else ""
            adults = session.get("adults", 1)
            print(f"[step8] dest={dest!r} depart={depart!r} ret={ret!r} custom={custom!r}")
            itinerary_msgs = []
            if dest and depart:
                try:
                    itinerary_msgs = build_itinerary_flex(
                        dest, depart, ret, city,
                        custom_requests=custom, budget=budget, adults=adults,
                    )
                except Exception as e:
                    print(f"[step8] itinerary error: {e}")
            summary_msgs = _prompt_summary(user_id)
            return (itinerary_msgs + summary_msgs)[:5]
        return _show_step_prompt(user_id, target_step)

    if "trip_select" in params:
        # 處理步驟內的選擇（例如選機票）
        return _handle_selection(user_id, params)

    # ── 說走就走的 postback ──
    if "quick_days" in params:
        from bot.handlers.quick_trip import _find_options
        return _find_options(user_id, int(params["quick_days"]))

    if "quick_pick" in params:
        from bot.handlers.quick_trip import handle_quick_pick
        return handle_quick_pick(user_id, int(params["quick_pick"]))

    return []


def _show_step_prompt(user_id: str, step: int) -> list:
    """顯示指定步驟的提示訊息"""
    prompts = {
        1: _prompt_destination,
        2: _prompt_dates,
        3: _prompt_travelers,
        4: _prompt_flights,
        5: _prompt_hotels,
        6: _prompt_itinerary,
        7: _prompt_travel_info,
        8: _prompt_summary,
    }
    fn = prompts.get(step)
    if fn:
        return fn(user_id)
    return [{"type": "text", "text": "\u898f\u5283\u5df2\u5b8c\u6210\uff01"}]


# ─── 步驟 1：目的地 ──────────────────────────────────

def _prompt_destination(user_id: str) -> list:
    return [{
        "type": "text", "text":
            f"[1/8] \u76ee\u7684\u5730\n\n"
            f"\u597d\u7684\uff01\u7b2c\u4e00\u6b65\uff1a\n\n"
            f"\u4f60\u9019\u6b21\u6700\u60f3\u53bb\u54ea\u500b\u570b\u5bb6\u6216\u57ce\u5e02\u5462\uff1f\n\n"
            f"\u53ef\u4ee5\u76f4\u63a5\u8f38\u5165\uff0c\u4f8b\u5982\uff1a\n"
            f"\u2022 \u65e5\u672c\u6771\u4eac\n"
            f"\u2022 \u6cf0\u570b\u66fc\u8c37\n"
            f"\u2022 \u97d3\u570b\u9996\u723e\n"
            f"\u2022 \u7fa9\u5927\u5229\u7f85\u99ac",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "\U0001f1ef\U0001f1f5 \u65e5\u672c", "text": "\u6771\u4eac"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f1f0\U0001f1f7 \u97d3\u570b", "text": "\u9996\u723e"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f1f9\U0001f1ed \u6cf0\u570b", "text": "\u66fc\u8c37"}},
                {"type": "action", "action": {"type": "message", "label": "\U0001f30d \u5e6b\u6211\u63a8\u85a6", "text": "\u63a8\u85a6\u76ee\u7684\u5730"}},
            ],
        },
    }]


def _parse_hints_from_text(text: str) -> dict:
    """從自然語言中萃取預算、天數、人數，回傳 dict（可能為空）。"""
    import re
    hints = {}

    # 預算：「一萬」「2萬」「30000」「10000台幣」
    cn_num = {"一": 1, "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    m = re.search(r"([一兩二三四五六七八九十\d]+)[萬]", text)
    if m:
        raw = m.group(1)
        val = cn_num.get(raw, None)
        if val is None:
            try:
                val = int(raw)
            except ValueError:
                val = None
        if val:
            hints["budget"] = val * 10000
    if "budget" not in hints:
        m = re.search(r"(\d{4,})\s*(?:台幣|元|TWD)?", text)
        if m:
            hints["budget"] = int(m.group(1))

    # 天數：「14天」「7天」「兩週」「一週」
    m = re.search(r"(\d+)\s*[天日]", text)
    if m:
        hints["duration_days"] = int(m.group(1))
    elif "兩週" in text or "两週" in text:
        hints["duration_days"] = 14
    elif "一週" in text or "1週" in text:
        hints["duration_days"] = 7

    # 人數：「4人」「三人」「2個人」
    m = re.search(r"([一兩二三四五六七八九\d]+)\s*[人個]", text)
    if m:
        raw = m.group(1)
        val = cn_num.get(raw, None)
        if val is None:
            try:
                val = int(raw)
            except ValueError:
                val = None
        if val and 1 <= val <= 20:
            hints["adults"] = val

    # 活動錨點偵測（演唱會/奧運/見面會等） → 改變 Step 2 問法
    _EVENT_KEYWORDS = (
        "演唱會", "見面會", "fan meeting", "fanmeet", "concert",
        "奧運", "世界盃", "博覽會", "EXPO", "expo", "展覽", "比賽",
        "世錦賽", "亞運", "世大運", "嘉年華",
    )
    if any(kw in text for kw in _EVENT_KEYWORDS):
        hints["is_event_trip"] = True

    # 行程風格關鍵字 → 預填 custom_requests
    _STYLE_HINTS = [
        (("最夯", "熱門玩法", "夯玩法"), "請加入當地最熱門玩法、打卡景點與特色體驗"),
        (("演唱會", "見面會", "fan meeting", "fanmeet", "concert",
          "追星", "K-POP", "KPOP", "kpop"),
         None),   # 活動行程的 custom_requests 在偵測到 event_date 後動態生成
        (("奧運", "世界盃", "博覽會", "EXPO", "expo", "展覽", "比賽",
          "世錦賽", "亞運", "世大運"),
         None),   # 同上
        (("美食", "必吃", "吃吃喝喝"), "美食為主：請以必吃餐廳和在地小吃為行程重點"),
        (("購物", "掃貨", "逛街"), "購物為主：請安排購物中心、藥妝、免稅店"),
        (("自然", "健行", "爬山"), "親近自然：請安排山岳健行、自然風景景點"),
        (("歷史", "文化", "古蹟"), "文化深度：請安排歷史古蹟、博物館、傳統文化體驗"),
        (("親子", "小孩", "帶小孩"), "親子行程：請安排適合兒童的景點與活動"),
        (("蜜月", "情侶", "兩人世界"), "浪漫行程：請安排適合情侶的景點、餐廳與夜景"),
    ]
    for kws, hint_text in _STYLE_HINTS:
        if any(kw in text for kw in kws):
            if hint_text:
                hints["custom_requests"] = hint_text
            break

    # 日期 → 預填，活動行程把解析到的日期存為 event_date（錨點）
    from bot.utils.date_parser import parse_date_range, parse_month
    depart, ret = parse_date_range(text)
    if depart:
        if hints.get("is_event_trip"):
            hints["event_date"] = depart
            # custom_requests 帶入活動日期資訊
            event_kw = next((kw for kw in _EVENT_KEYWORDS if kw in text), "活動")
            hints["custom_requests"] = (
                f"行程核心是 {depart} 的{event_kw}，"
                f"請以當天場館周邊安排活動日行程，其餘天自由探索城市"
            )
        else:
            hints["depart_date"] = depart
            if ret:
                hints["return_date"] = ret
            hints["flexibility"] = "specific"
    else:
        month = parse_month(text)
        if month:
            hints["depart_date"] = month
            hints["flexibility"] = "month"

    return hints


def _step1_destination(user_id: str, text: str) -> list:
    from bot.utils.date_parser import parse_destination_keyword, parse_destination
    from bot.constants.cities import IATA_TO_NAME, IATA_TO_COUNTRY, CITY_FLAG

    if text in ("推薦目的地", "幫我推薦"):
        from bot.handlers.explore import handle_quick_explore
        session = get_session(user_id)
        origin = session.get("origin", "TPE") if session else "TPE"
        return handle_quick_explore(origin) + [
            {"type": "text", "text": "看到喜歡的目的地了嗎？請直接輸入城市名即可繼續規劃！"}
        ]

    hints = _parse_hints_from_text(text)

    # ── 先用關鍵字比對（確定） ──
    dest_code = parse_destination_keyword(text)
    if dest_code:
        city_name = IATA_TO_NAME.get(dest_code, dest_code)
        country_code = IATA_TO_COUNTRY.get(dest_code, "")
        update_session(user_id, {
            "destination_code": dest_code,
            "destination_name": city_name,
            "country_code": country_code,
            **hints,
        }, step=2)
        return _after_destination_set(user_id, city_name, hints)

    # ── 關鍵字失敗 → LLM 猜，但顯示確認而非靜默設定 ──
    llm_code = parse_destination(text)   # 這裡才呼叫 LLM
    if llm_code:
        city_name = IATA_TO_NAME.get(llm_code, llm_code)
        flag = CITY_FLAG.get(llm_code, "🌍")
        is_event = hints.get("is_event_trip", False)
        update_session(user_id, {
            "destination_code": llm_code,
            "destination_name": city_name,
            "country_code": IATA_TO_COUNTRY.get(llm_code, ""),
            **hints,
        }, step=2)
        if is_event:
            event_kw = next(
                (kw for kw in ("演唱會", "見面會", "奧運", "比賽", "博覽會", "展覽")
                 if kw in text), "活動"
            )
            return [{
                "type": "text",
                "text": f"{event_kw}在哪個城市/場館呢？\n\n"
                        f"我猜可能是 {flag} {city_name}，對嗎？\n\n"
                        f"（不同城市場館差很多，請確認一下）",
                "quickReply": {"items": [
                    {"type": "action", "action": {"type": "message",
                        "label": f"✅ 對，在{city_name}", "text": city_name}},
                    {"type": "action", "action": {"type": "message",
                        "label": "❌ 不對", "text": "推薦目的地"}},
                ]},
            }]
        return [{
            "type": "text",
            "text": f"我猜你要去的是 {flag} {city_name}，對嗎？\n\n"
                    f"如果不對，請直接輸入正確的城市名稱。",
            "quickReply": {"items": [
                {"type": "action", "action": {"type": "message",
                    "label": f"✅ 對，去{city_name}", "text": city_name}},
                {"type": "action", "action": {"type": "message",
                    "label": "❌ 不對，換一個", "text": "推薦目的地"}},
            ]},
        }]

    # ── LLM 也猜不到 → 直接問 ──
    print(f"[dest_unknown] text={repr(text[:60])}")
    return [{
        "type": "text",
        "text": "你想去哪個城市呢？\n\n直接輸入城市名稱就可以，例如：",
        "quickReply": {"items": [
            {"type": "action", "action": {"type": "message", "label": "🇯🇵 東京", "text": "東京"}},
            {"type": "action", "action": {"type": "message", "label": "🇰🇷 首爾", "text": "首爾"}},
            {"type": "action", "action": {"type": "message", "label": "🇺🇸 洛杉磯", "text": "洛杉磯"}},
            {"type": "action", "action": {"type": "message", "label": "🇹🇭 曼谷", "text": "曼谷"}},
            {"type": "action", "action": {"type": "message", "label": "🌍 幫我推薦", "text": "推薦目的地"}},
        ]},
    }]


def _after_destination_set(user_id: str, city_name: str, hints: dict) -> list:
    """目的地確認後，根據是否預填日期決定下一步提示。"""
    if hints.get("depart_date"):
        return _prompt_dates(user_id)
    return [{
        "type": "text", "text":
            f"[2/8] 日期\n\n"
            f"目的地：{city_name} ✅\n\n"
            f"第二步：你預計什麼時候出發？\n\n"
            f"請選擇或輸入：\n"
            f"• 直接輸入日期，例如「6/15-6/22」\n"
            f"• 或輸入月份，例如「6月」",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "彈性日期", "text": "彈性"}},
                {"type": "action", "action": {"type": "message", "label": "下個月", "text": "下個月"}},
            ],
        },
    }]

    return [{
        "type": "text", "text":
            f"[2/8] \u65e5\u671f\n\n"
            f"\u76ee\u7684\u5730\uff1a{city_name} \u2705\n\n"
            f"\u7b2c\u4e8c\u6b65\uff1a\u4f60\u9810\u8a08\u4ec0\u9ebc\u6642\u5019\u51fa\u767c\uff1f\n\n"
            f"\u8acb\u9078\u64c7\u6216\u8f38\u5165\uff1a\n"
            f"\u2022 \u76f4\u63a5\u8f38\u5165\u65e5\u671f\uff0c\u4f8b\u5982\u300c6/15-6/22\u300d\n"
            f"\u2022 \u6216\u8f38\u5165\u6708\u4efd\uff0c\u4f8b\u5982\u300c6\u6708\u300d",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "\u4e0b\u9031", "text": "\u4e0b\u9031"}},
                {"type": "action", "action": {"type": "message", "label": "\u4e0b\u500b\u6708", "text": "\u4e0b\u500b\u6708"}},
                {"type": "action", "action": {"type": "message", "label": "\u6700\u8fd1\u6709\u5047\u5c31\u8d70", "text": "\u5f48\u6027"}},
                {"type": "action", "action": {"type": "message", "label": "\u6691\u5047", "text": "7\u6708"}},
                {"type": "action", "action": {"type": "message", "label": "\u5e74\u5e95", "text": "12\u6708"}},
            ],
        },
    }]


# ─── 步驟 2：日期 ────────────────────────────────────

def _prompt_dates(user_id: str) -> list:
    import datetime
    session = get_session(user_id) or {}
    city = session.get("destination_name", "")
    pre_depart = session.get("depart_date", "")
    pre_ret = session.get("return_date", "")
    event_date = session.get("event_date", "")

    # 活動錨點模式：問幾天前到、幾天後離開
    if event_date:
        try:
            ed = datetime.date.fromisoformat(event_date)
            ed_str = f"{ed.month}/{ed.day}"
        except Exception:
            ed_str = event_date
        event_kw = session.get("custom_requests", "活動")[:6]

        def _make_option(label: str, before: int, after: int) -> dict:
            try:
                dep = (ed - datetime.timedelta(days=before)).isoformat()
                ret = (ed + datetime.timedelta(days=after)).isoformat()
                return {"type": "action", "action": {"type": "message",
                    "label": label, "text": f"{dep}-{ret}"}}
            except Exception:
                return {"type": "action", "action": {"type": "message",
                    "label": label, "text": label}}

        update_session(user_id, {}, step=3)
        return [{
            "type": "text",
            "text": f"[2/8] 行程天數\n\n"
                    f"📅 {event_kw[:10]} 日期：{ed_str}\n\n"
                    f"你想幾天前抵達、活動後停留幾天？",
            "quickReply": {"items": [
                _make_option(f"前1天到 · 後1天離", 1, 1),
                _make_option(f"前1天到 · 後2天離", 1, 2),
                _make_option(f"前2天到 · 後1天離", 2, 1),
                _make_option(f"前2天到 · 後2天離", 2, 2),
                {"type": "action", "action": {"type": "message",
                    "label": "自訂日期", "text": "自訂日期"}},
            ]},
        }]

    # 日期已從初始訊息預填 → 直接確認並跳到 Step 3
    if pre_depart:
        flex = session.get("flexibility", "specific")
        if flex == "month":
            date_str = f"{pre_depart}（月份）"
        elif pre_ret:
            date_str = f"{pre_depart} → {pre_ret}"
        else:
            date_str = pre_depart
        update_session(user_id, {}, step=3)
        return [{"type": "text", "text":
            f"[2/8] 日期\n\n"
            f"目的地：{city} ✅\n"
            f"日期：{date_str} ✅（從你的訊息自動帶入）\n\n"
            f"如需修改，請直接輸入新日期；否則繼續下一步：",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "✅ 日期正確，繼續", "text": "繼續"}},
                    {"type": "action", "action": {"type": "message", "label": "修改日期", "text": "修改日期"}},
                ],
            },
        }] + _prompt_travelers(user_id)

    return [{"type": "text", "text":
        f"[2/8] 日期\n\n"
        f"目的地：{city}\n\n"
        f"你預計什麼時候出發？\n"
        f"例如：「6/15-6/22」或「6月」",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "彈性日期", "text": "彈性"}},
                {"type": "action", "action": {"type": "message", "label": "下個月", "text": "下個月"}},
            ],
        },
    }]


def _step2_dates(user_id: str, text: str) -> list:
    from bot.utils.date_parser import parse_date_range, parse_month
    import datetime

    session = get_session(user_id) or {}

    if text in ("\u5f48\u6027", "\u6700\u8fd1\u6709\u5047\u5c31\u8d70"):
        today = datetime.date.today()
        next_month = f"{today.year}-{today.month + 1:02d}" if today.month < 12 else f"{today.year + 1}-01"
        update_session(user_id, {
            "flexibility": "flexible",
            "depart_date": next_month,
            "return_date": "",
        }, step=3)
        return _prompt_travelers(user_id)

    if text == "\u4e0b\u500b\u6708":
        today = datetime.date.today()
        next_month = f"{today.year}-{today.month + 1:02d}" if today.month < 12 else f"{today.year + 1}-01"
        update_session(user_id, {
            "flexibility": "month",
            "depart_date": next_month,
            "return_date": "",
        }, step=3)
        return _prompt_travelers(user_id)

    # 嘗試解析月份
    month = parse_month(text)
    if month and not parse_date_range(text)[0]:
        update_session(user_id, {
            "flexibility": "month",
            "depart_date": month,
            "return_date": "",
        }, step=3)
        return _prompt_travelers(user_id)

    # 嘗試解析日期範圍
    depart, ret = parse_date_range(text)
    if depart:
        # 若只有出發日但 session 有天數，自動算回程
        if not ret:
            session = get_session(user_id) or {}
            days = session.get("duration_days")
            if days:
                import datetime
                d = datetime.date.fromisoformat(depart)
                ret = (d + datetime.timedelta(days=days - 1)).isoformat()
        update_session(user_id, {
            "flexibility": "specific",
            "depart_date": depart,
            "return_date": ret,
        }, step=3)
        return _prompt_travelers(user_id)

    return [{"type": "text", "text":
        "\u6211\u770b\u4e0d\u61c2\u65e5\u671f\uff0c\u8acb\u8a66\u8a66\uff1a\n"
        "\u300c6/15-6/22\u300d\u300c7\u6708\u300d\u300c\u4e0b\u500b\u6708\u300d"
    }]


# ─── 步驟 3：人數與預算 ──────────────────────────────

def _prompt_travelers(user_id: str) -> list:
    session = get_session(user_id) or {}
    city = session.get("destination_name", "")
    dates = session.get("depart_date", "")
    flex = session.get("flexibility", "")

    date_display = dates
    if flex == "flexible":
        date_display = "\u5f48\u6027\u65e5\u671f"
    elif flex == "month" and dates:
        date_display = f"{dates[5:]}\u6708"

    return [{
        "type": "text", "text":
            f"[3/8] \u4eba\u6578\u8207\u9810\u7b97\n\n"
            f"\u76ee\u7684\u5730\uff1a{city}\n"
            f"\u65e5\u671f\uff1a{date_display}\n\n"
            f"\u7b2c\u4e09\u6b65\uff1a\u9019\u6b21\u7e3d\u5171\u6709\u5e7e\u500b\u4eba\u8981\u53bb\u5462\uff1f",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "1 人獨旅", "text": "1人"}},
                {"type": "action", "action": {"type": "message", "label": "2 人同行", "text": "2人"}},
                {"type": "action", "action": {"type": "message", "label": "3 人", "text": "3人"}},
                {"type": "action", "action": {"type": "message", "label": "4 人", "text": "4人"}},
                {"type": "action", "action": {"type": "message", "label": "5人以上", "text": "5人"}},
            ],
        },
    }]


def _step3_travelers(user_id: str, text: str) -> list:
    import re

    # 解析人數
    m = re.search(r"(\d+)", text)
    if not m:
        return [{"type": "text", "text": "\u8acb\u544a\u8a34\u6211\u4eba\u6578\uff0c\u4f8b\u5982\uff1a\u300c2\u4eba\u300d"}]

    adults = int(m.group(1))
    session = get_session(user_id) or {}

    # 如果還沒問預算，先存人數再問預算
    if not session.get("budget"):
        update_session(user_id, {"adults": adults, "children": 0})
        # 若人數已從第一句話萃取，此處 adults 從 text 再確認
        hint_budget = session.get("budget")
        if hint_budget:
            # 預算已在 session，直接跳進票務搜尋
            return _prompt_budget_response(user_id, str(hint_budget))
        return [{
            "type": "text", "text":
                f"好的，{adults} 人出發！\n\n"
                f"這趟旅行的總預算大約是多少？（台幣）\n\n"
                f"不知道的話，可以點「幫我估算」，我會根據目的地幫你算出建議金額。",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "💡 幫我估算", "text": "幫我估預算"}},
                    {"type": "action", "action": {"type": "message", "label": "3萬以下", "text": "預算3萬"}},
                    {"type": "action", "action": {"type": "message", "label": "3~6萬", "text": "預算6萬"}},
                    {"type": "action", "action": {"type": "message", "label": "6~10萬", "text": "預算10萬"}},
                    {"type": "action", "action": {"type": "message", "label": "10~20萬", "text": "預算15萬"}},
                    {"type": "action", "action": {"type": "message", "label": "20萬以上", "text": "預算25萬"}},
                ],
            },
        }]

    return _prompt_budget_response(user_id, text)


def _suggest_budget(user_id: str) -> list:
    """根據目的地+天數+人數自動估算預算，並詢問是否採用"""
    import datetime
    from bot.utils.budget_estimator import estimate_budget, build_budget_bubble
    from bot.constants.cities import CITY_FLAG

    session = get_session(user_id) or {}
    dest = session.get("destination_code", "")
    city = session.get("destination_name", dest)
    flag = CITY_FLAG.get(dest, "✈️")
    adults = session.get("adults", 1)
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")

    # 計算天數
    days = session.get("duration_days") or 5
    if depart and ret:
        try:
            d1 = datetime.date.fromisoformat(depart[:10])
            d2 = datetime.date.fromisoformat(ret[:10])
            days = max((d2 - d1).days + 1, 1)
        except Exception:
            pass

    # 機票粗估：用目的地最低預算的 60%
    flight_pp = int(_MIN_BUDGET_PER_PERSON.get(dest, 30000) * 0.6)

    b = estimate_budget(dest, days, adults, flight_pp)
    recommended = int(b["total"] * 1.2 / 10000 + 0.5) * 10000  # 無條件進位到萬

    bubble = build_budget_bubble(dest, city, days, adults, flight_pp, flag)

    return [
        {"type": "flex", "altText": f"💰 {city} 預估旅費明細",
         "contents": bubble},
        {"type": "text",
         "text": f"📊 建議預備預算：NT$ {recommended:,}\n（含安全餘裕 ×1.2）\n\n要用這個預算繼續規劃嗎？",
         "quickReply": {"items": [
             {"type": "action", "action": {"type": "message",
              "label": "✅ 用建議預算", "text": f"預算{recommended // 10000}萬"}},
             {"type": "action", "action": {"type": "message",
              "label": "自己輸入金額", "text": "自訂預算"}},
         ]}},
    ]


def _prompt_budget_response(user_id: str, text: str) -> list:
    """解析預算並進入步驟 4（自動搜尋機票）"""
    import re

    if text in ("幫我估預算", "幫我估算", "不知道", "幫我算"):
        return _suggest_budget(user_id)

    budget_map = {
        # 舊格式（向下相容）
        "5萬以下": 50000, "預算5萬": 50000,
        "5-10萬": 100000, "預算10萬": 100000,
        "10-15萬": 150000, "預算15萬": 150000,
        "15萬以上": 200000, "預算20萬": 200000,
        # 新格式
        "預算3萬": 30000, "3萬以下": 30000,
        "預算6萬": 60000, "3~6萬": 60000,
        "6~10萬": 100000,
        "10~20萬": 150000,
        "預算25萬": 250000, "20萬以上": 250000,
    }

    budget = budget_map.get(text)
    if not budget:
        m = re.search(r"(\d+)", text)
        if m:
            num = int(m.group(1))
            budget = num * 10000 if num < 1000 else num
        else:
            budget = 100000

    session = get_session(user_id) or {}
    flight_confirmed = session.get("flight_confirmed", False)
    update_session(user_id, {"budget": budget}, step=5 if flight_confirmed else 4)

    # 預算合理性檢查
    warning = _check_budget_warning(user_id, budget)
    if warning:
        return [warning]   # 先給警告，等用戶確認後繼續

    # 已從機票卡片選定航班 → 跳過機票搜尋，直接安排住宿
    if flight_confirmed:
        session = get_session(user_id) or {}
        dest = session.get("destination_name", "")
        depart = session.get("depart_date", "")
        ret = session.get("return_date", "")
        return [{"type": "text", "text":
            f"✅ 機票已選定（{depart[5:10].replace('-','/')} → {ret[5:10].replace('-','/') if ret else '單程'}）\n\n接下來幫你安排住宿和行程！"}
        ] + _prompt_hotels(user_id)

    return _prompt_flights(user_id)


# 目的地 → 每人最低合理預算（台幣）
_MIN_BUDGET_PER_PERSON = {
    "LAX": 80000, "NYC": 90000, "SFO": 85000, "SEA": 80000,
    "YVR": 75000, "YTO": 80000,
    "LON": 80000, "PAR": 85000, "ROM": 80000, "FRA": 75000,
    "AMS": 75000, "VIE": 75000, "PRG": 70000, "ZRH": 90000,
    "IST": 55000, "BCN": 75000,
    "SYD": 75000, "MEL": 75000, "AKL": 80000,
    "DXB": 60000,
    "TYO": 40000, "OSA": 38000, "SEL": 30000,
    "BKK": 25000, "SIN": 35000, "KUL": 20000,
    "DPS": 22000, "MNL": 20000, "SGN": 20000,
    "HKG": 28000, "MFM": 28000,
}


def _check_budget_warning(user_id: str, budget: int) -> dict | None:
    """若預算明顯不足，回傳警告訊息，否則回傳 None。"""
    session = get_session(user_id) or {}
    dest = session.get("destination_code", "")
    adults = session.get("adults", 1)
    min_per_person = _MIN_BUDGET_PER_PERSON.get(dest, 0)
    if not min_per_person:
        return None

    min_total = min_per_person * adults
    if budget >= min_total * 0.7:   # 留 30% 容錯
        return None

    city = session.get("destination_name", dest)
    return {
        "type": "text",
        "text": (
            f"⚠️ 預算提醒\n\n"
            f"{adults} 人去 {city}，預算 NT${budget:,} 可能不夠——\n"
            f"光機票來回每人就約 NT${min_per_person // 10000 * 10000:,} 起。\n\n"
            f"建議至少準備 NT${min_total:,} 以上。\n\n"
            f"要調整預算，還是就這樣繼續？"
        ),
        "quickReply": {"items": [
            {"type": "action", "action": {"type": "message",
                "label": f"調整為 {min_total // 10000}萬",
                "text": f"預算{min_total // 10000}萬"}},
            {"type": "action", "action": {"type": "message",
                "label": "就這樣繼續", "text": "繼續規劃"}},
        ]},
    }


# ─── 步驟 4：機票推薦 ────────────────────────────────

def _prompt_flights(user_id: str) -> list:
    """根據 session 資料搜尋機票並顯示推薦"""
    from bot.config import TRAVELPAYOUTS_TOKEN
    from bot.constants.cities import IATA_TO_NAME, TW_AIRPORTS
    from bot.services.travelpayouts import search_flights, search_cheapest_by_month
    from bot.utils.url_builder import skyscanner_url, google_flights_url
    from bot.flex.flight_bubble import flight_bubble

    session = get_session(user_id) or {}
    origin = session.get("origin", "TPE")
    dest = session.get("destination_code", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    flex = session.get("flexibility", "specific")
    budget = session.get("budget", 0)
    adults = session.get("adults", 1)
    city_name = session.get("destination_name", dest)

    if not dest:
        return [{"type": "text", "text": "\u627e\u4e0d\u5230\u76ee\u7684\u5730\u8cc7\u8a0a\uff0c\u8acb\u8f38\u5165\u300c\u53d6\u6d88\u898f\u5283\u300d\u91cd\u65b0\u958b\u59cb"}]

    # 搜尋機票
    flights = None
    try:
        if TRAVELPAYOUTS_TOKEN:
            if flex == "month":
                flights = search_cheapest_by_month(origin, depart)
                if flights:
                    flights = [f for f in flights if f.get("destination") == dest]
            elif depart:
                flights = search_flights(origin, dest, depart, ret)
    except Exception as e:
        print(f"[flights] search error dest={dest}: {e}")
        flights = None

    if not flights:
        update_session(user_id, {}, step=5)
        sky = skyscanner_url(origin, dest, depart or "", ret or "")
        gf = google_flights_url(origin, dest, depart or "", ret or "")
        msgs = [{"type": "text", "text":
            f"[4/8] 機票推薦\n\n"
            f"✈️ 即時票價暫時無法取得，跳過機票步驟。\n"
            f"🔍 Skyscanner：{sky}\n"
            f"🔍 Google Flights：{gf}"
        }]
        # LINE 上限 5 則，hotels 最多 3 則，合計控制在 4 則以內
        hotel_msgs = _prompt_hotels(user_id)
        return (msgs + hotel_msgs)[:4]

    # 排序：價格低到高
    flights.sort(key=lambda x: x.get("price", 99999))

    # 如果有預算限制，標記超出預算的
    per_person_budget = budget // adults if adults > 0 else budget

    # 取前 5 個
    top_flights = flights[:5]

    # 建立機票卡片（帶「選這個」postback 按鈕）
    bubbles = []
    for i, f in enumerate(top_flights):
        price = f.get("price", 0)
        bubble = flight_bubble(f, i, show_track_btn=False)

        # 替換 footer：加入「選這個」按鈕
        flight_id = f"{f.get('airline', '')}-{f.get('departure_at', '')}-{price}"
        select_btn = {
            "type": "button", "style": "primary", "color": "#FF6B35", "height": "sm",
            "action": {
                "type": "postback",
                "label": "\u2705 \u9078\u9019\u500b\u65b9\u6848",
                "data": f"trip_select=flight&idx={i}&price={price}&airline={f.get('airline', '')}",
                "displayText": f"\u6211\u9078\u64c7\u65b9\u6848 {i+1}",
            },
        }

        # 預算提示
        if per_person_budget > 0 and price > per_person_budget:
            bubble["body"]["contents"].append({
                "type": "text", "text": "\u26a0\ufe0f \u8d85\u51fa\u4eba\u5747\u9810\u7b97",
                "size": "xs", "color": "#E53935", "margin": "sm",
            })
        elif per_person_budget > 0 and price <= per_person_budget * 0.7:
            bubble["body"]["contents"].append({
                "type": "text", "text": "\U0001f4b0 \u6027\u50f9\u6bd4\u6975\u9ad8",
                "size": "xs", "color": "#4CAF50", "margin": "sm",
            })

        # 在 footer 最前面加入選擇按鈕
        bubble["footer"]["contents"].insert(0, select_btn)
        bubbles.append(bubble)

    # 加一張「跳過」卡片
    bubbles.append({
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical",
            "justifyContent": "center", "alignItems": "center",
            "paddingAll": "20px", "spacing": "md",
            "contents": [
                {"type": "text", "text": "\u23ed\ufe0f", "size": "3xl", "align": "center"},
                {"type": "text", "text": "\u5148\u8df3\u904e\u6a5f\u7968", "weight": "bold", "size": "md", "align": "center"},
                {"type": "text", "text": "\u7a0d\u5f8c\u518d\u6c7a\u5b9a\u6a5f\u7968",
                 "size": "sm", "color": "#888888", "align": "center", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px",
            "contents": [
                {"type": "button", "style": "secondary", "height": "sm",
                 "action": {"type": "postback", "label": "\u8df3\u904e\uff0c\u7e7c\u7e8c\u4f4f\u5bbf",
                            "data": "trip_step=5", "displayText": "\u8df3\u904e\u6a5f\u7968"}},
            ],
        },
    })

    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    date_display = _format_dates(session)

    # 儲存搜尋到的機票資料（供後續使用）
    update_session(user_id, {"flight_results": [
        {"price": f.get("price"), "airline": f.get("airline"), "transfers": f.get("transfers"),
         "departure_at": f.get("departure_at"), "return_at": f.get("return_at"),
         "origin": f.get("origin"), "destination": f.get("destination")}
        for f in top_flights
    ]})

    return [
        {"type": "text", "text":
            f"[4/8] \u6a5f\u7968\u63a8\u85a6\n\n"
            f"\u2708\ufe0f {origin_name} \u2192 {city_name}\n"
            f"\U0001f4c5 {date_display}\n"
            f"\U0001f465 {adults} \u4eba\n\n"
            f"\u6839\u64da\u4f60\u7684\u689d\u4ef6\uff0c\u627e\u5230\u4ee5\u4e0b\u6a5f\u7968\u65b9\u6848\uff1a\n"
            f"\uff08\u5de6\u53f3\u6ed1\u52d5\u67e5\u770b\u66f4\u591a\uff0c\u9ede\u300c\u9078\u9019\u500b\u65b9\u6848\u300d\u7e7c\u7e8c\uff09"
        },
        {
            "type": "flex",
            "altText": f"{city_name} \u6a5f\u7968\u63a8\u85a6",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def _step4_flights(user_id: str, text: str) -> list:
    """步驟 4：使用者可能在此步驟輸入文字（通常是透過 postback 選擇）"""
    # 如果使用者直接打字，跳到下一步
    update_session(user_id, {}, step=5)
    return _prompt_hotels(user_id)


# ─── 步驟 5：住宿推薦 ────────────────────────────────

def _prompt_hotels(user_id: str) -> list:
    """根據目的地和日期產生多平台飯店連結"""
    from bot.constants.cities import IATA_TO_NAME, AGODA_CITY_KEYWORDS
    from bot.utils.url_builder import agoda_url, booking_url
    from bot.handlers.hotels import _get_estimate

    session = get_session(user_id) or {}
    dest = session.get("destination_code", "")
    city_name = session.get("destination_name", dest)
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    city_kw = AGODA_CITY_KEYWORDS.get(dest, city_name)
    date_display = _format_dates(session)
    est = _get_estimate(dest)

    agoda = agoda_url(city_kw, depart, ret)
    booking = booking_url(city_kw)

    # Trip.com 連結
    trip_com = f"https://www.trip.com/hotels/?city={city_kw}&locale=zh-TW&curr=TWD"

    return [
        {
            "type": "flex",
            "altText": f"[5/8] {city_name} \u4f4f\u5bbf\u63a8\u85a6",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#E91E8C", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": f"\U0001f3e8 {city_name} \u4f4f\u5bbf\u63a8\u85a6",
                         "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                        {"type": "text", "text": f"\U0001f4c5 {date_display}",
                         "color": "#FFE0CC", "size": "sm", "margin": "xs"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "md", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "\u4f60\u504f\u597d\u4f4f\u5728\u54ea\u500b\u5340\u57df\uff1f",
                         "weight": "bold", "size": "md"},
                        # 估算資訊卡
                        {
                            "type": "box", "layout": "horizontal",
                            "backgroundColor": "#FFF0F5", "paddingAll": "10px",
                            "cornerRadius": "8px", "margin": "sm",
                            "contents": [
                                {"type": "box", "layout": "vertical", "flex": 1, "contents": [
                                    {"type": "text", "text": "\U0001f4b0 \u4f30\u7b97\u5468\u5747",
                                     "size": "xxs", "color": "#C2185B", "weight": "bold"},
                                    {"type": "text", "text": f"NT$ {est['price']}/\u6674",
                                     "size": "xs", "color": "#333333", "weight": "bold"},
                                ]},
                                {"type": "box", "layout": "vertical", "flex": 1, "contents": [
                                    {"type": "text", "text": "\u2b50 \u8a55\u5206",
                                     "size": "xxs", "color": "#C2185B", "weight": "bold"},
                                    {"type": "text", "text": est["rating"],
                                     "size": "xs", "color": "#333333", "weight": "bold"},
                                ]},
                                {"type": "box", "layout": "vertical", "flex": 2, "contents": [
                                    {"type": "text", "text": "\U0001f4cd \u63a8\u85a6\u5340\u57df",
                                     "size": "xxs", "color": "#C2185B", "weight": "bold"},
                                    {"type": "text", "text": est["area"],
                                     "size": "xxs", "color": "#555555", "wrap": True},
                                ]},
                            ],
                        },
                        {"type": "separator"},
                        {"type": "text", "text": "\U0001f4b0 \u53f0\u7063\u4eba\u6700\u611b\u7528\u7684\u8a02\u623f\u5e73\u53f0",
                         "size": "sm", "color": "#999999", "margin": "md"},
                    ],
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "10px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#E91E8C", "height": "sm",
                         "action": {"type": "uri", "label": "\U0001f3e8 Agoda \u8a02\u98ef\u5e97", "uri": agoda}},
                        {"type": "button", "style": "primary", "color": "#003580", "height": "sm",
                         "action": {"type": "uri", "label": "\U0001f3e8 Booking.com", "uri": booking}},
                        {"type": "button", "style": "primary", "color": "#2577E3", "height": "sm",
                         "action": {"type": "uri", "label": "\U0001f3e8 Trip.com", "uri": trip_com}},
                        {"type": "separator", "margin": "md"},
                        {"type": "button", "style": "secondary", "height": "sm",
                         "action": {"type": "postback", "label": "\u2705 \u5df2\u770b\u904e\uff0c\u4e0b\u4e00\u6b65\uff1a\u884c\u7a0b",
                                    "data": "trip_step=6", "displayText": "\u7e7c\u7e8c\u898f\u5283\u884c\u7a0b"}},
                    ],
                },
            },
        },
        {
            "type": "text", "text":
                "\U0001f4a1 \u5c0f\u63d0\u793a\uff1a\n"
                "\u2022 \u5148\u700f\u89bd\u4ee5\u4e0a\u5e73\u53f0\u6bd4\u50f9\n"
                "\u2022 \u770b\u5b8c\u5f8c\u9ede\u300c\u5df2\u770b\u904e\uff0c\u4e0b\u4e00\u6b65\u300d\u7e7c\u7e8c\n"
                "\u2022 \u6216\u76f4\u63a5\u8f38\u5165\u4f60\u504f\u597d\u7684\u5340\u57df\uff08\u5982\u300c\u5e02\u4e2d\u5fc3\u300d\u300c\u8fd1\u8eca\u7ad9\u300d\uff09",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "\U0001f3d9\ufe0f \u5e02\u4e2d\u5fc3", "text": "\u5e02\u4e2d\u5fc3"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f689 \u8fd1\u8eca\u7ad9", "text": "\u8fd1\u8eca\u7ad9"}},
                    {"type": "action", "action": {"type": "message", "label": "\U0001f4b0 \u4fbf\u5b9c\u512a\u5148", "text": "\u4fbf\u5b9c\u512a\u5148"}},
                    {"type": "action", "action": {"type": "postback", "label": "\u27a1\ufe0f \u8df3\u904e", "data": "trip_step=6", "displayText": "\u8df3\u904e\u4f4f\u5bbf"}},
                ],
            },
        },
    ]


def _step5_hotels(user_id: str, text: str) -> list:
    """步驟 5：記錄住宿偏好，進入步驟 6"""
    preference = text.strip()
    if preference:
        update_session(user_id, {"hotel_preference": preference}, step=6)
    else:
        update_session(user_id, {}, step=6)
    return _prompt_itinerary(user_id)


# ─── 步驟 6：行程大綱 ────────────────────────────────

def _prompt_itinerary(user_id: str) -> list:
    session = get_session(user_id) or {}
    city = session.get("destination_name", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    pre_filled = session.get("custom_requests", "")

    days = _calc_days(depart, ret)
    days_text = f"{days} 天" if days > 0 else "彈性天數"

    if pre_filled:
        # 已從初始訊息偵測到行程偏好，直接顯示並讓用戶確認或修改
        return [{
            "type": "text", "text":
                f"[6/8] 行程大綱\n\n"
                f"目的地：{city}\n"
                f"天數：{days_text}\n\n"
                f"✅ 我已記住你的行程偏好：\n「{pre_filled}」\n\n"
                f"可以直接點「繼續」讓我規劃，或輸入其他想法來調整：",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "✅ 就這樣，繼續", "text": pre_filled}},
                    {"type": "action", "action": {"type": "message", "label": "🏰 熱門景點", "text": "熱門景點"}},
                    {"type": "action", "action": {"type": "message", "label": "🍜 美食為主", "text": "美食為主"}},
                    {"type": "action", "action": {"type": "message", "label": "🤖 幫我規劃", "text": "幫我規劃"}},
                ],
            },
        }]

    return [{
        "type": "text", "text":
            f"[6/8] 行程大綱\n\n"
            f"目的地：{city}\n"
            f"天數：{days_text}\n\n"
            f"有沒有特別想去的景點或想避開的？\n\n"
            f"可以告訴我，例如：\n"
            f"• 「想去迪士尼」\n"
            f"• 「想逃避觀光客」\n"
            f"• 「美食為主」\n\n"
            f"或點「幫我規劃」由我自動安排",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "🏰 熱門景點", "text": "熱門景點"}},
                {"type": "action", "action": {"type": "message", "label": "🍜 美食為主", "text": "美食為主"}},
                {"type": "action", "action": {"type": "message", "label": "🛍️ 購物行程", "text": "購物行程"}},
                {"type": "action", "action": {"type": "message", "label": "🤖 幫我規劃", "text": "幫我規劃"}},
            ],
        },
    }]


def _step6_itinerary(user_id: str, text: str) -> list:
    update_session(user_id, {"custom_requests": text.strip()}, step=7)
    return _prompt_travel_info(user_id)


# ─── 步驟 7：行前須知 ────────────────────────────────

def _prompt_travel_info(user_id: str) -> list:
    """產出完整行前須知（旅遊警示+簽證+海關+文化+天氣+匯率+打包）"""
    from bot.services.travel_data import get_visa_info, get_customs_info, get_cultural_notes, get_packing_list
    from bot.services.weather_api import get_weather
    from bot.services.exchange_api import get_exchange_rate
    from bot.constants.countries import COUNTRY_CURRENCY, COUNTRY_NAME
    from bot.services.policy_checker import get_live_advisory

    session = get_session(user_id) or {}
    country = session.get("country_code", "")
    city = session.get("destination_name", "")
    dest = session.get("destination_code", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    country_name = COUNTRY_NAME.get(country, city)

    bubbles = []

    # ── Bubble 0: 旅遊警示（Level 3/4 才顯示，置頂）──
    if country:
        advisory = get_live_advisory(country)
        if advisory and advisory.get("level", 0) >= 3:
            level = advisory["level"]
            level_text = advisory.get("level_text", f"第{level}級")
            summary = advisory.get("summary", "")
            bg_color = "#D32F2F" if level >= 4 else "#E65100"
            icon = "🔴" if level >= 4 else "🟠"
            warning_lines = [
                f"{icon} 外交部旅遊警示：{level_text}",
                "",
                f"⚠️ 台灣外交部對 {advisory.get('country', country_name)} 發布旅遊警示",
            ]
            if summary:
                warning_lines.append(f"\n{summary[:80]}")
            warning_lines.append("\n🔗 詳情請查詢外交部領事事務局")
            bubbles.append(_info_bubble(
                f"⚠️ 旅遊警示 {level_text}",
                "\n".join(warning_lines),
                bg_color,
            ))

    # ── Bubble 1: 簽證 ──
    visa = get_visa_info(country)
    if visa:
        visa_status = "\u2705 \u514d\u7c3d" if visa.get("visa_required") is False else f"\u26a0\ufe0f {visa.get('visa_required', '\u9700\u7c3d\u8b49')}"
        visa_text = (
            f"{visa_status}\n"
            f"\u505c\u7559\uff1a{visa.get('stay_limit', 'N/A')}\n"
            f"\u8b77\u7167\uff1a{visa.get('passport_validity', 'N/A')}\n"
            f"\u5099\u8a3b\uff1a{visa.get('notes', '')}"
        )
        bubbles.append(_info_bubble("\U0001f4d8 \u7c3d\u8b49\u8cc7\u8a0a", visa_text, "#1565C0"))

    # ── Bubble 2: 海關禁品 ──
    customs = get_customs_info(country)
    if customs:
        prohibited = customs.get("prohibited_in", [])
        duty_free = customs.get("duty_free", {})
        important = customs.get("important", [])

        customs_lines = ["\u274c \u7981\u6b62\u651c\u5e36\u5165\u5883\uff1a"]
        for item in prohibited[:5]:
            customs_lines.append(f"  \u2022 {item}")
        if duty_free:
            customs_lines.append("\n\u2705 \u514d\u7a05\u984d\u5ea6\uff1a")
            for k, v in list(duty_free.items())[:4]:
                customs_lines.append(f"  \u2022 {k}: {v}")
        if important:
            warnings = important if isinstance(important, list) else [important]
            for w in warnings[:2]:
                customs_lines.append(f"\n\u26a0\ufe0f {w}")

        bubbles.append(_info_bubble("\U0001f6c3 \u6d77\u95dc\u7981\u54c1", "\n".join(customs_lines), "#E53935"))

    # ── Bubble 3: 文化注意事項 ──
    culture = get_cultural_notes(country)
    if culture:
        tips = culture.get("tips", [])
        culture_lines = []
        for tip in tips[:6]:
            culture_lines.append(f"\u2022 {tip}")
        if culture.get("plug_type"):
            culture_lines.append(f"\n\U0001f50c \u63d2\u5ea7\uff1a{culture['plug_type']}")
        if culture.get("payment"):
            culture_lines.append(f"\U0001f4b3 {culture['payment']}")
        if culture.get("transport_tip"):
            culture_lines.append(f"\U0001f689 {culture['transport_tip']}")

        bubbles.append(_info_bubble("\U0001f30d \u6587\u5316\u5c0f\u63d0\u9192", "\n".join(culture_lines), "#6A1B9A"))

    # ── Bubble 4: 天氣 ──
    weather = get_weather(dest, depart, ret) if depart else None
    if weather:
        weather_text = (
            f"\U0001f321\ufe0f \u6e29\u5ea6\uff1a{weather['avg_low']}\u00b0C ~ {weather['avg_high']}\u00b0C\n"
            f"\U0001f327\ufe0f \u964d\u96e8\u6a5f\u7387\uff1a{weather['rain_chance']}%\n"
            f"\U0001f4ac {weather['description']}"
        )
        bubbles.append(_info_bubble("\u2600\ufe0f \u5929\u6c23\u9810\u5831", weather_text, "#FF9800"))

    # ── Bubble 5: 匯率 ──
    currency_code = COUNTRY_CURRENCY.get(country, "")
    exchange = get_exchange_rate(currency_code) if currency_code else None
    if exchange:
        exchange_text = (
            f"\U0001f4b1 {exchange['display']}\n"
            f"\U0001f4b0 {exchange['example']}\n"
            f"\U0001f4c5 \u8cc7\u6599\u65e5\u671f\uff1a{exchange.get('date', 'N/A')}"
        )
        bubbles.append(_info_bubble("\U0001f4b1 \u532f\u7387\u8cc7\u8a0a", exchange_text, "#2E7D32"))

    # ── Bubble 6: 打包清單 ──
    month = int(depart[5:7]) if depart and len(depart) >= 7 else 6
    packing = get_packing_list(country, month)
    if packing:
        pack_lines = ["\U0001f4c4 \u8b49\u4ef6\uff1a"]
        for item in packing["documents"][:4]:
            pack_lines.append(f"  \u2610 {item}")
        if packing["climate_items"]:
            pack_lines.append(f"\n\U0001f321\ufe0f {packing['climate_label']}\uff1a")
            for item in packing["climate_items"][:4]:
                pack_lines.append(f"  \u2610 {item}")
        if packing["country_items"]:
            pack_lines.append(f"\n\U0001f1f9\U0001f1fc {country_name}\u5c08\u7528\uff1a")
            for item in packing["country_items"][:4]:
                pack_lines.append(f"  \u2610 {item}")

        bubbles.append(_info_bubble("\U0001f9f3 \u6253\u5305\u6e05\u55ae", "\n".join(pack_lines), "#5C6BC0"))

    # 如果什麼資料都沒有
    if not bubbles:
        return [{
            "type": "text", "text":
                f"[7/8] \u884c\u524d\u9808\u77e5\n\n"
                f"\u62b1\u6b49\uff0c\u76ee\u524d\u9084\u6c92\u6709 {city} \u7684\u8a73\u7d30\u884c\u524d\u8cc7\u8a0a\u3002\n"
                f"\u5efa\u8b70\u4f60\u67e5\u8a62\u5916\u4ea4\u90e8\u9818\u4e8b\u4e8b\u52d9\u5c40\u7db2\u7ad9\u3002",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "postback", "label": "\u27a1\ufe0f \u4e0b\u4e00\u6b65", "data": "trip_step=8", "displayText": "\u7e7c\u7e8c"}},
                ],
            },
        }]

    messages = [
        {"type": "text", "text":
            f"[7/8] \u884c\u524d\u9808\u77e5\n\n"
            f"\u4ee5\u4e0b\u662f {city}({country_name}) \u7684\u91cd\u8981\u884c\u524d\u8cc7\u8a0a\uff1a\n"
            f"\u2190 \u5de6\u53f3\u6ed1\u52d5\u67e5\u770b\u5168\u90e8"},
        {
            "type": "flex",
            "altText": f"{city} \u884c\u524d\u9808\u77e5",
            "contents": {"type": "carousel", "contents": bubbles},
        },
        {
            "type": "text", "text":
                "\u26a0\ufe0f \u4ee5\u4e0a\u8cc7\u8a0a\u50c5\u4f9b\u53c3\u8003\uff0c\u8acb\u4ee5\u5404\u570b\u5b98\u65b9\u516c\u544a\u70ba\u6e96\u3002\n\n"
                "\u9ede\u300c\u4e0b\u4e00\u6b65\u300d\u7522\u51fa\u5b8c\u6574\u8a08\u756b\u66f8\uff01",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "postback", "label": "\u27a1\ufe0f \u7522\u51fa\u8a08\u756b\u66f8", "data": "trip_step=8", "displayText": "\u7522\u51fa\u8a08\u756b\u66f8"}},
                ],
            },
        },
    ]

    return messages


def _info_bubble(title: str, content: str, color: str) -> dict:
    """通用資訊卡片"""
    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": color, "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": title, "color": "#FFFFFF", "weight": "bold", "size": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "sm",
            "contents": [
                {"type": "text", "text": content, "size": "sm", "color": "#444444", "wrap": True},
            ],
        },
    }


def _step7_travel_info(user_id: str, text: str) -> list:
    update_session(user_id, {}, step=8)
    # 行程大綱 + 計畫書合併輸出
    from bot.utils.itinerary_builder import build_itinerary_flex
    session = get_session(user_id) or {}
    dest = session.get("destination_code", "")
    city = session.get("destination_name", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    _budget_num = session.get("budget", 0)
    budget = f"NT${_budget_num//10000}萬" if _budget_num else ""
    adults = session.get("adults", 1)
    custom = session.get("custom_requests", "")
    print(f"[step7] dest={dest!r} depart={depart!r} ret={ret!r} custom={custom!r}")
    itinerary_msgs = []
    if dest and depart:
        try:
            itinerary_msgs = build_itinerary_flex(
                dest, depart, ret, city,
                custom_requests=custom, budget=budget, adults=adults,
            )
        except Exception as e:
            print(f"[step7] itinerary error: {e}")
    summary_msgs = _prompt_summary(user_id)
    return (itinerary_msgs + summary_msgs)[:5]


# ─── 步驟 8：完整計畫書（Phase 5 完整實作）───────────

def _prompt_summary(user_id: str) -> list:
    """產出完整計畫書"""
    from bot.constants.cities import IATA_TO_NAME, TW_AIRPORTS, CITY_FLAG, IATA_TO_COUNTRY
    from bot.constants.airlines import airline_name
    from bot.constants.countries import COUNTRY_NAME, COUNTRY_CURRENCY
    from bot.services.travel_data import get_visa_info, get_customs_info, get_cultural_notes
    from bot.services.weather_api import get_weather
    from bot.services.exchange_api import get_exchange_rate
    from bot.utils.url_builder import skyscanner_url, google_flights_url, agoda_url, booking_url

    session = get_session(user_id) or {}
    city = session.get("destination_name", "\u672a\u8a2d\u5b9a")
    dest = session.get("destination_code", "")
    origin = session.get("origin", "TPE")
    country = session.get("country_code", "")
    origin_name = {v: k for k, v in TW_AIRPORTS.items()}.get(origin, origin)
    date_display = _format_dates(session)
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")
    adults = session.get("adults", 1)
    budget = session.get("budget", 0)
    hotel_pref = session.get("hotel_preference", "")
    custom = session.get("custom_requests", "")
    flag = CITY_FLAG.get(dest, "\u2708\ufe0f")
    days = _calc_days(depart, ret)
    days_text = f"{days}\u5929{days-1}\u591c" if days > 1 else "\u5f48\u6027\u5929\u6578"
    country_name = COUNTRY_NAME.get(country, "")

    # 機票資訊
    flight_choice = session.get("flight_choice")
    flight_results = session.get("flight_results", [])
    if flight_choice:
        flight_text = f"NT${flight_choice.get('price', 0):,} ({airline_name(flight_choice.get('airline', ''))})"
    elif flight_results:
        f = flight_results[0]
        flight_text = f"NT${f.get('price', 0):,} ({airline_name(f.get('airline', ''))})"
    else:
        flight_text = "\u5c1a\u672a\u9078\u64c7"

    # 簽證摘要
    visa = get_visa_info(country)
    visa_text = ""
    if visa:
        visa_text = "\u2705 \u514d\u7c3d" if visa.get("visa_required") is False else f"\u26a0\ufe0f {visa.get('visa_required')}"
        visa_text += f"({visa.get('stay_limit', '')})"

    # 天氣摘要
    weather = get_weather(dest, depart, ret) if depart else None
    weather_text = ""
    if weather:
        weather_text = f"{weather['avg_low']}-{weather['avg_high']}\u00b0C, \u964d\u96e8{weather['rain_chance']}%"

    # 匯率摘要
    currency_code = COUNTRY_CURRENCY.get(country, "")
    exchange = get_exchange_rate(currency_code) if currency_code else None
    exchange_text = exchange["example"] if exchange else ""

    # 文化摘要
    culture = get_cultural_notes(country)
    culture_highlights = ""
    if culture:
        plug = culture.get("plug_type", "")
        culture_highlights = f"\U0001f50c {plug}" if plug else ""

    # ── 建立計畫書 Flex Message ──
    # 摘要卡片
    summary_body = [
        {"type": "text", "text": f"{flag} {city} {days_text}", "weight": "bold", "size": "lg"},
        {"type": "separator", "margin": "md"},
        _summary_row("\u2708\ufe0f \u8def\u7dda", f"{origin_name} \u2192 {city}"),
        _summary_row("\U0001f4c5 \u65e5\u671f", date_display),
        _summary_row("\U0001f465 \u4eba\u6578", f"{adults} \u4eba"),
        _summary_row("\U0001f4b0 \u9810\u7b97", f"NT${budget:,}"),
        {"type": "separator", "margin": "md"},
        _summary_row("\u2708\ufe0f \u6a5f\u7968", flight_text),
        _summary_row("\U0001f3e8 \u4f4f\u5bbf", hotel_pref or "\u672a\u8a2d\u5b9a"),
    ]

    if visa_text:
        summary_body.append(_summary_row("\U0001f4d8 \u7c3d\u8b49", visa_text))
    if weather_text:
        summary_body.append(_summary_row("\u2600\ufe0f \u5929\u6c23", weather_text))
    if exchange_text:
        summary_body.append(_summary_row("\U0001f4b1 \u532f\u7387", exchange_text))
    if culture_highlights:
        summary_body.append(_summary_row("\U0001f50c \u63d2\u5ea7", culture_highlights))
    if custom:
        summary_body.append({"type": "separator", "margin": "md"})
        summary_body.append(_summary_row("\U0001f4dd \u5099\u8a3b", custom))

    summary_body.append({"type": "separator", "margin": "md"})
    summary_body.append({
        "type": "text", "text": "\u26a0\ufe0f \u7c3d\u8b49/\u6d77\u95dc\u8cc7\u8a0a\u50c5\u4f9b\u53c3\u8003\uff0c\u8acb\u4ee5\u5b98\u65b9\u516c\u544a\u70ba\u6e96",
        "size": "xxs", "color": "#999999", "wrap": True, "margin": "md",
    })
    summary_body.append({"type": "separator", "margin": "md"})
    summary_body.append({
        "type": "text",
        "text": "\u2b06\ufe0f \u8a08\u756b\u66f8\u4e0a\u65b9\u9084\u6709\uff1a\u5929\u5929\u884c\u7a0b\u5361\u7247\u00b7\u884c\u524d\u9808\u77e5\uff0c\u5de6\u53f3\u6ed1\u52d5\u67e5\u770b",
        "size": "xs", "color": "#E91E63", "weight": "bold", "wrap": True, "margin": "sm",
    })

    # 訂票連結
    footer_buttons = []
    if dest and depart:
        footer_buttons.append({
            "type": "button", "style": "primary", "color": "#00B0F0", "height": "sm",
            "action": {"type": "uri", "label": "\U0001f50d \u53bb Skyscanner \u8a02\u7968",
                       "uri": skyscanner_url(origin, dest, depart, ret)},
        })
        from bot.constants.cities import AGODA_CITY_KEYWORDS
        city_kw = AGODA_CITY_KEYWORDS.get(dest, city)
        footer_buttons.append({
            "type": "button", "style": "primary", "color": "#E91E8C", "height": "sm",
            "action": {"type": "uri", "label": "\U0001f3e8 \u53bb Agoda \u8a02\u623f",
                       "uri": agoda_url(city_kw, depart, ret)},
        })

    # 產生下載 token，存行程資料到 Redis（72 小時）
    import uuid
    from bot.services.redis_store import redis_set
    import json as _json

    download_token = uuid.uuid4().hex
    plan_data = {
        "flag": flag, "city": city, "days_text": days_text,
        "origin_name": origin_name, "date_display": date_display,
        "adults": adults, "budget": budget,
        "flight_text": flight_text,
        "hotel_pref": hotel_pref,
        "visa_text": visa_text,
        "weather_text": weather_text,
        "exchange_text": exchange_text,
        "plug_text": culture_highlights,
        "custom": custom,
        "must_eat": _get_must_eat(dest),
        "itinerary": _get_itinerary_for_download(dest, depart, ret),
    }
    redis_set(f"download:{download_token}", _json.dumps(plan_data, ensure_ascii=False), ttl=259200)

    # 取得 Vercel 部署 URL
    vercel_url = "https://abroad-uturn.vercel.app"
    download_url = f"{vercel_url}/api/download?token={download_token}"

    footer_buttons.append({
        "type": "button", "style": "secondary", "height": "sm",
        "action": {"type": "uri", "label": "📥 下載行程計畫書 (.docx)",
                   "uri": download_url},
    })
    footer_buttons.extend([
        {"type": "button", "style": "secondary", "height": "sm",
         "action": {"type": "message", "label": "🔄 重新規劃", "text": "開始規劃"}},
        {"type": "button", "style": "secondary", "height": "sm",
         "action": {"type": "message", "label": "🌍 探索其他目的地", "text": "便宜"}},
    ])

    # ── 預估支出 Bubble ──
    from bot.utils.budget_estimator import build_budget_bubble
    flight_price = 0
    if flight_choice:
        flight_price = flight_choice.get("price", 0)
    elif session.get("flight_results"):
        flight_price = session["flight_results"][0].get("price", 0)
    budget_bubble = None
    if dest and days > 0 and flight_price > 0:
        budget_bubble = build_budget_bubble(dest, city, days, adults, flight_price, flag)

    # 儲存回饋排程（回程後 D+1 push 滿意度問卷）
    if ret and dest:
        try:
            import json as _json
            from bot.services.redis_store import redis_set
            _feedback_data = _json.dumps({"city": city, "dest": dest, "return_date": ret, "days": days, "adults": adults})
            redis_set(f"feedback:{user_id}", _feedback_data, ttl=60 * 60 * 24 * 30)
        except Exception:
            pass

    # 清除 session（規劃完成）
    clear_session(user_id)

    msgs = [
        {
            "type": "flex",
            "altText": f"\u2705 {city} {days_text} \u51fa\u570b\u8a08\u756b\u66f8",
            "contents": {
                "type": "bubble", "size": "mega",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#FF6B35", "paddingAll": "18px",
                    "contents": [
                        {"type": "text", "text": f"\U0001f389 \u4f60\u7684\u51fa\u570b\u8a08\u756b\u5b8c\u6210\uff01",
                         "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                        {"type": "text", "text": f"{flag} {city} {days_text}",
                         "color": "#FFE0CC", "size": "md", "margin": "xs"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": summary_body,
                },
                "footer": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "10px",
                    "contents": footer_buttons,
                },
            },
        },
    ]

    if budget_bubble:
        msgs.append({
            "type": "flex",
            "altText": f"💰 {city} 預估旅遊支出",
            "contents": budget_bubble,
        })

    return msgs


def _get_must_eat(dest_code: str) -> list:
    """取得目的地必吃清單（供下載用）"""
    try:
        from bot.utils.itinerary_builder import _get_template
        tmpl = _get_template(dest_code)
        return tmpl.get("must_eat", [])
    except Exception:
        return []


def _get_itinerary_for_download(dest_code: str, depart: str, ret: str) -> list:
    """取得天天行程資料（供下載用，純文字格式）"""
    try:
        import datetime
        from bot.utils.itinerary_builder import _get_template, _calc_days
        tmpl = _get_template(dest_code)
        if not tmpl:
            return []
        days = _calc_days(depart, ret)
        full_days = tmpl.get("full_days", [])
        result = []
        for day_num in range(1, days + 1):
            date_label = ""
            if depart:
                try:
                    d = datetime.date.fromisoformat(depart[:10])
                    actual = d + datetime.timedelta(days=day_num - 1)
                    date_label = f"{actual.month}/{actual.day}"
                except Exception:
                    pass
            if day_num == 1:
                plan = tmpl.get("arrival", {})
                title = f"Day {day_num} 抵達"
            elif day_num == days:
                plan = tmpl.get("departure", {})
                title = f"Day {day_num} 返台"
            else:
                idx = (day_num - 2) % max(len(full_days), 1)
                plan = full_days[idx] if full_days else {}
                title = f"Day {day_num} {plan.get('theme', '深度探索')}"
            result.append({
                "title": title,
                "date_label": date_label,
                "am": plan.get("am", ""),
                "pm": plan.get("pm", ""),
                "eve": plan.get("eve", ""),
            })
        return result
    except Exception:
        return []


def _summary_row(label: str, value: str) -> dict:
    return {
        "type": "box", "layout": "horizontal", "margin": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#888888", "flex": 3},
            {"type": "text", "text": value, "size": "sm", "color": "#333333", "flex": 7, "wrap": True},
        ],
    }


def _step8_summary(user_id: str, text: str) -> list:
    return _prompt_summary(user_id)


def _handle_selection(user_id: str, params: dict) -> list:
    """處理步驟內的選擇 postback"""
    select_type = params.get("trip_select", "")

    if select_type == "flight":
        # 使用者選了一個機票方案
        idx = int(params.get("idx", 0))
        price = params.get("price", "0")
        airline_code = params.get("airline", "")

        session = get_session(user_id) or {}
        flight_results = session.get("flight_results", [])
        chosen = flight_results[idx] if idx < len(flight_results) else {}

        from bot.constants.airlines import airline_name
        airline_display = airline_name(airline_code)

        update_session(user_id, {
            "flight_choice": chosen,
            "flight_choice_display": f"NT${int(price):,} ({airline_display})",
        }, step=5)

        return [
            {"type": "text", "text":
                f"\u2705 \u5df2\u9078\u64c7\u6a5f\u7968\uff1a{airline_display} NT${int(price):,}\n\n"
                f"\u63a5\u4e0b\u4f86\u5e6b\u4f60\u627e\u4f4f\u5bbf\uff01"
            },
        ] + _prompt_hotels(user_id)

    return [{"type": "text", "text": "\u5df2\u6536\u5230\u4f60\u7684\u9078\u64c7\uff01"}]


# ─── 工具函數 ────────────────────────────────────────

def _format_dates(session: dict) -> str:
    """格式化日期顯示"""
    flex = session.get("flexibility", "")
    depart = session.get("depart_date", "")
    ret = session.get("return_date", "")

    if flex == "flexible":
        return "\u5f48\u6027\u65e5\u671f"
    elif flex == "month" and depart:
        return f"{depart[5:]}\u6708"
    elif depart and ret:
        d = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
        r = ret[5:].replace("-", "/") if len(ret) >= 10 else ret
        return f"{d} ~ {r}"
    elif depart:
        d = depart[5:].replace("-", "/") if len(depart) >= 10 else depart
        return d
    return "\u672a\u8a2d\u5b9a"


def _calc_days(depart: str, ret: str) -> int:
    """計算旅行天數"""
    if not depart or not ret or len(depart) < 10 or len(ret) < 10:
        return 0
    try:
        import datetime
        d1 = datetime.date.fromisoformat(depart[:10])
        d2 = datetime.date.fromisoformat(ret[:10])
        return (d2 - d1).days + 1
    except Exception:
        return 0
