"""訊息路由（取代舊 handle_text_message）"""

from bot.session.manager import get_session, get_step, clear_session
from bot.handlers.settings import get_user_origin
from bot.handlers import trip_flow


def route_text(text: str, user_id: str) -> list:
    """主要文字訊息路由"""
    text = text.strip()
    origin = get_user_origin(user_id)

    # ── 1. 全域指令（不管在不在規劃中都能用）──
    if text == "我的ID":
        return [{"type": "text", "text":
            f"你的 LINE User ID：\n{user_id}\n\n"
            "複製後貼到 Vercel → Settings → Environment Variables\n"
            "變數名稱：ADMIN_USER_ID"}]

    if text in ("取消規劃", "重新開始"):
        clear_session(user_id)
        return [{"type": "text", "text": "\u2705 \u5df2\u53d6\u6d88\u898f\u5283\uff0c\u96a8\u6642\u53ef\u4ee5\u91cd\u65b0\u958b\u59cb\uff01"}]

    if text in ("繼續規劃", "繼續"):
        step = get_step(user_id)
        if step == 4:
            return trip_flow._prompt_flights(user_id)
        if step > 0:
            return trip_flow._show_step_prompt(user_id, step)
        return [{"type": "text", "text": "你目前沒有進行中的規劃。輸入「開始規劃」開始吧！"}]

    # ── 出發地設定 ──
    if "出發地" in text or text in ("設定出發地", "出發機場", "改出發地"):
        from bot.handlers.settings import handle_set_origin
        return handle_set_origin(user_id, text)

    # ── 開始/重啟規劃（含按鈕帶驚嘆號的變體）──
    if text in ("開始規劃", "開始規劃！", "完整出國規劃", "規劃旅程", "重新規劃"):
        clear_session(user_id)
        return trip_flow.start(user_id)

    # ── 說走就走：等待特別需求的自由文字輸入 ──
    session = get_session(user_id) or {}
    if "quick_pending_pick" in session:
        from bot.handlers.quick_trip import handle_quick_pick
        idx = session["quick_pending_pick"]
        return handle_quick_pick(user_id, idx, custom=text)

    # ── Rich Menu 精確按鈕（不進計分，保持即時回應）──
    if text in ("說走就走", "說走就飛", "馬上飛", "快速規劃"):
        from bot.handlers.quick_trip import handle_quick_trip
        return handle_quick_trip(user_id, text)

    if text == "設定":
        current = get_user_origin(user_id)
        name_map = {"TPE": "桃園國際", "TSA": "台北松山", "KHH": "高雄國際", "RMQ": "台中清泉崗", "TNN": "台南"}
        current_name = name_map.get(current, current)
        return [{
            "type": "flex",
            "altText": "⚙️ 設定",
            "contents": {
                "type": "bubble", "size": "kilo",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#37474F", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "⚙️ 設定",
                         "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                        {"type": "text", "text": f"出發地：{current_name} ({current})",
                         "color": "#B0BEC5", "size": "sm"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#FF6B35", "height": "sm",
                         "action": {"type": "message", "label": "✈️ 變更出發地", "text": "出發地"}},
                        {"type": "button", "style": "secondary", "height": "sm",
                         "action": {"type": "message", "label": "📖 使用說明", "text": "使用說明"}},
                    ],
                },
            },
        }]

    # ── 機票卡片「立刻規劃行程」帶目的地+日期直接進規劃（必須在 session 判斷前）──
    if text.startswith("規劃行程|"):
        parts = text.split("|")
        dest_code = parts[1] if len(parts) > 1 else ""
        depart = parts[2] if len(parts) > 2 else ""
        ret = parts[3] if len(parts) > 3 else ""
        if dest_code and depart:
            return trip_flow.start_with_flight(user_id, dest_code, depart, ret)

    # ── 2. 檢查是否有進行中的規劃 session ──
    step = get_step(user_id)
    if step > 0:
        # 偵測「新規劃意圖」：若輸入明顯是全新旅程，清掉舊 session 重來
        _NEW_TRIP_SIGNALS = ("規劃", "幫我", "想去", "帶我去", "出國", "行程", "旅行")
        from bot.utils.date_parser import parse_destination
        from bot.session.manager import clear_session as _clear
        has_dest = bool(parse_destination(text))
        has_signal = any(kw in text for kw in _NEW_TRIP_SIGNALS)
        if has_dest and has_signal:
            _clear(user_id)
            step = 0  # 當作無 session 繼續往下處理
        else:
            # 在規劃流程中，處理預算相關輸入
            session = get_session(user_id) or {}
            if step == 3 and session.get("adults") and not session.get("budget"):
                return trip_flow._prompt_budget_response(user_id, text)
            return trip_flow.handle_step(user_id, text, step)

    # ── 3. 精確指令（按鈕觸發，不進計分）──
    if text in ("開始規劃", "我要規劃旅行", "完整出國規劃", "規劃旅程", "旅行規劃"):
        return trip_flow.start(user_id)

    if text in ("我的旅行計畫", "我的計畫", "旅行計畫"):
        from bot.handlers.my_plans import handle_my_plans
        return handle_my_plans(user_id)

    if text in ("選月份",):
        from bot.flex.month_picker import month_picker_flex
        return month_picker_flex()

    if text.startswith("探索|"):
        from bot.handlers.explore import handle_explore
        return handle_explore(text.split("|")[1], origin)

    if text.startswith("行前 ") or text.startswith("行前|"):
        from bot.handlers.pre_trip import handle_pre_trip_country
        return handle_pre_trip_country(text, user_id)

    if text.startswith("追蹤|"):
        from bot.handlers.tracking import handle_track
        return handle_track(user_id, text)

    if text.startswith("取消追蹤"):
        from bot.handlers.tracking import handle_cancel_track
        return handle_cancel_track(user_id, text)

    # ── 4. 計分路由（自由文字）──
    from bot.utils.intent import classify_intent
    from bot.handlers.explore import (
        handle_quick_explore, handle_compare, handle_direct_flights,
        handle_transfer_cheapest, handle_flexible_dates, handle_package,
        handle_popular_countries,
    )
    from bot.utils.date_parser import parse_destination, parse_date_range

    intent = classify_intent(text)

    if intent == "plan_trip":
        return trip_flow.start_smart(user_id, text)

    if intent == "compare":
        dest = parse_destination(text)
        if dest:
            return handle_compare(text, origin)
        return handle_quick_explore(origin)

    if intent == "explore":
        if "直飛" in text:
            return handle_direct_flights(origin)
        if "轉機" in text:
            return handle_transfer_cheapest(origin)
        if "機加酒" in text:
            return handle_package(text.replace("機加酒", "").strip(), origin)
        if "熱門" in text:
            return handle_popular_countries(origin)
        if "彈性" in text:
            return handle_flexible_dates(text.replace("彈性日期", "").replace("彈性", "").strip(), origin)
        return handle_quick_explore(origin)

    if intent == "visa":
        from bot.handlers.visa import handle_visa
        return handle_visa(text, user_id)

    if intent == "transport":
        from bot.handlers.transport import handle_transport
        return handle_transport(text, user_id)

    if intent == "hotel":
        from bot.handlers.hotels import handle_hotels
        return handle_hotels(text, user_id)

    if intent == "souvenir":
        from bot.handlers.souvenirs import handle_souvenirs
        return handle_souvenirs(text, user_id)

    if intent == "idol":
        from bot.handlers.idol_trip import handle_idol_trip
        return handle_idol_trip(text, user_id)

    if intent == "pre_trip":
        from bot.handlers.pre_trip import handle_pre_trip_menu, handle_pre_trip_country
        dest = parse_destination(text)
        if dest:
            return handle_pre_trip_country(text, user_id)
        return handle_pre_trip_menu()

    if intent == "tracking":
        from bot.handlers.tracking import handle_my_tracks
        return handle_my_tracks(user_id)

    if intent == "help":
        return build_help_message()

    # ── 5. unknown → 智慧偵測城市名 → 體驗關鍵字 → LLM fallback ──
    dest = parse_destination(text)
    if dest:
        depart, ret = parse_date_range(text)
        if depart:
            return handle_compare(text, origin)
        return trip_flow.start_with_destination(user_id, text)

    experience = _match_experience(text)
    if experience:
        return experience

    return _llm_intent_fallback(text, user_id)


def route_postback(data: str, user_id: str) -> list:
    """處理 postback 事件"""
    return trip_flow.handle_postback(user_id, data)


def _build_toolbox() -> list:
    return [{
        "type": "flex",
        "altText": "\u65c5\u884c\u5de5\u5177\u7bb1",
        "contents": {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#5C6BC0", "paddingAll": "15px",
                "contents": [
                    {"type": "text", "text": "\U0001f9f3 \u65c5\u884c\u5de5\u5177\u7bb1",
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "15px",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#FF6B35", "height": "sm",
                     "action": {"type": "message", "label": "\u2728 \u5b8c\u6574\u51fa\u570b\u898f\u5283", "text": "\u958b\u59cb\u898f\u5283"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "\U0001f6eb \u8a2d\u5b9a\u51fa\u767c\u5730", "text": "\u51fa\u767c\u5730"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "\U0001f4c5 \u9078\u6708\u4efd\u63a2\u7d22", "text": "\u63a2\u7d22\u6700\u4fbf\u5b9c"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "\U0001f514 \u6211\u7684\u8ffd\u8e64\u6e05\u55ae", "text": "\u6211\u7684\u8ffd\u8e64"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "\U0001f4d6 \u4f7f\u7528\u6559\u5b78", "text": "\u4f7f\u7528\u6559\u5b78"}},
                ],
            },
        },
    }]


def build_welcome_message() -> list:
    return [{
        "type": "flex",
        "altText": "\u6b61\u8fce\u4f86\u5230\u51fa\u570b\u512a\u8f49\uff01",
        "contents": {
            "type": "bubble", "size": "mega",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#FF6B35", "paddingAll": "20px",
                "contents": [
                    {"type": "text", "text": "\u2708\ufe0f \u6b61\u8fce\u4f86\u5230\u51fa\u570b\u512a\u8f49\uff01",
                     "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "AbroadUturn - \u53f0\u7063\u4eba\u5c08\u5c6c\u7684\u51fa\u570b\u65c5\u7a0b\u898f\u5283\u5e2b",
                     "color": "#FFE0CC", "size": "sm", "margin": "sm"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "lg", "paddingAll": "20px",
                "contents": [
                    {"type": "text", "text": "\U0001f30d \u6211\u80fd\u5e6b\u4f60\u505a\u4ec0\u9ebc\uff1f", "weight": "bold", "size": "md"},
                    {"type": "separator"},
                    {"type": "text", "text":
                        "\u2705 \u5b8c\u6574\u51fa\u570b\u898f\u5283\uff088 \u6b65\u5e36\u4f60\u8d70\u5b8c\uff09\n"
                        "\u2705 \u63a2\u7d22\u6700\u4fbf\u5b9c\u7684\u51fa\u570b\u76ee\u7684\u5730\n"
                        "\u2705 \u591a\u5e73\u53f0\u6a5f\u7968\u6bd4\u50f9\uff08\u542b\u7a05\u50f9\uff09\n"
                        "\u2705 \u7c3d\u8b49\u3001\u6d77\u95dc\u3001\u6587\u5316\u884c\u524d\u9808\u77e5\n"
                        "\u2705 \u50f9\u683c\u964d\u5e45\u5373\u6642\u901a\u77e5",
                     "size": "sm", "color": "#555555", "wrap": True},
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "15px",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#FF6B35",
                     "action": {"type": "message", "label": "\u2728 \u958b\u59cb\u898f\u5283\u65c5\u7a0b",
                                "text": "\u958b\u59cb\u898f\u5283"}},
                    {"type": "button", "style": "secondary",
                     "action": {"type": "message", "label": "\U0001f30d \u5148\u770b\u770b\u54ea\u88e1\u4fbf\u5b9c",
                                "text": "\u4fbf\u5b9c"}},
                    {"type": "button", "style": "secondary",
                     "action": {"type": "message", "label": "\U0001f6eb \u8a2d\u5b9a\u51fa\u767c\u5730",
                                "text": "\u51fa\u767c\u5730"}},
                ],
            },
        },
    }]


def build_help_message() -> list:
    return [{"type": "text", "text":
        "\u2708\ufe0f \u51fa\u570b\u512a\u8f49 \u4f7f\u7528\u6559\u5b78\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\u2728 \u5b8c\u6574\u65c5\u7a0b\u898f\u5283\n"
        "\u8f38\u5165\u300c\u958b\u59cb\u898f\u5283\u300d\n"
        "\u2192 8 \u6b65\u5e36\u4f60\u7522\u51fa\u5b8c\u6574\u51fa\u570b\u8a08\u756b\n\n"
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


_EXPERIENCE_MAP = [
    (("極光", "北極光", "aurora"),
     "🌌 極光通常在冰島、挪威、芬蘭才看得到！\n要幫你規劃去看極光嗎？",
     [("🇮🇸 冰島", "冰島"), ("🇳🇴 挪威", "挪威特羅姆瑟"), ("🇫🇮 芬蘭", "芬蘭羅瓦涅米")]),

    (("富士山", "賞楓", "賞櫻", "溫泉旅行", "和風"),
     "🗻 聽起來你想要道地的日本體驗！",
     [("🇯🇵 東京", "東京"), ("🇯🇵 京都", "京都"), ("🇯🇵 大阪", "大阪")]),

    (("海島", "潛水", "浮潛", "沙灘", "海灘", "度假村"),
     "🏖️ 想去海島放鬆！推薦幾個熱門選擇：",
     [("🇮🇩 峇里島", "峇里島"), ("🇵🇭 宿霧", "宿霧"), ("🇹🇭 普吉島", "普吉島")]),

    (("賭場", "賭博", "澳門"),
     "🎰 想去賭場玩？這幾個地方可以考慮：",
     [("🇲🇴 澳門", "澳門"), ("🇸🇬 新加坡", "新加坡")]),

    (("購物", "血拼", "名牌", "outlet"),
     "🛍️ 想購物血拼！這幾個城市最適合：",
     [("🇰🇷 首爾", "首爾"), ("🇯🇵 東京", "東京"), ("🇸🇬 新加坡", "新加坡")]),

    (("美食", "吃貨", "必吃", "街頭小吃"),
     "🍜 想吃遍當地美食！推薦美食天堂：",
     [("🇹🇭 曼谷", "曼谷"), ("🇯🇵 大阪", "大阪"), ("🇹🇼 台南", "台南")]),

    (("蜜月", "求婚", "情侶", "浪漫"),
     "💑 規劃浪漫旅程！這幾個地方很適合：",
     [("🇫🇷 巴黎", "巴黎"), ("🇮🇩 峇里島", "峇里島"), ("🇯🇵 京都", "京都")]),

    (("親子", "帶小孩", "迪士尼", "樂園", "遊樂園"),
     "👨‍👩‍👧 親子旅遊首選：",
     [("🇯🇵 東京", "東京"), ("🇭🇰 香港", "香港"), ("🇸🇬 新加坡", "新加坡")]),

    (("滑雪", "雪地", "看雪"),
     "⛷️ 想去玩雪！這幾個地方雪況最好：",
     [("🇯🇵 北海道", "北海道"), ("🇰🇷 首爾", "首爾"), ("🇨🇭 瑞士", "蘇黎世")]),
]


def _match_experience(text: str) -> list | None:
    """偵測體驗型關鍵字，直接推薦目的地，不需要 LLM。"""
    for keywords, reply_text, destinations in _EXPERIENCE_MAP:
        if any(kw in text for kw in keywords):
            quick_items = [
                {"type": "action", "action": {
                    "type": "message", "label": label, "text": dest}}
                for label, dest in destinations
            ]
            quick_items.append({"type": "action", "action": {
                "type": "message", "label": "✏️ 自己輸入", "text": "開始規劃"}})
            return [{"type": "text", "text": reply_text,
                     "quickReply": {"items": quick_items[:13]}}]
    return None


def _llm_intent_fallback(text: str, user_id: str) -> list:
    """用 Claude Haiku 理解意圖，引導到正確功能；LLM 失敗才降回靜態提示。"""
    import os
    # 記錄所有進入 fallback 的輸入，方便日後批量檢視
    print(f"[fallback] user={user_id[:8]} text={repr(text[:80])}")

    try:
        import anthropic
    except ImportError:
        print(f"[fallback] no_anthropic → static")
        return _static_fallback()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(f"[fallback] no_api_key → static")
        return _static_fallback()

    prompt = f"""你是台灣出國旅遊 LINE Bot「出國優轉」的意圖分類器。
使用者輸入：「{text}」

判斷規則：
- 只要輸入含有「出國」「國外」「出發」「旅行」「旅遊」「去哪」「想去」「飛」等字，優先判斷為 PLAN_TRIP
- 模糊或不確定時，傾向判斷為 PLAN_TRIP，不要輕易判斷 UNKNOWN
- 只有完全和旅遊無關（如問天氣、數學題、生活瑣事）才判斷 UNKNOWN

只回傳以下其中一個代碼（不要其他文字）：
- PLAN_TRIP      想規劃出國旅程（有目的地或泛泛想出國）
- FIND_CHEAP     想找便宜目的地或比價
- PRE_TRIP       想查簽證、海關、匯率、行前準備
- IDOL           追星、看演唱會、見面會
- TRANSPORT      交通卡、當地交通
- HOTEL          住宿、飯店
- SOUVENIR       伴手禮、必買
- HELP           詢問怎麼使用這個 Bot
- UNKNOWN        完全與旅遊無關（例如：問天氣、數學、健康問題）"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
        )
        intent = msg.content[0].text.strip().upper()
        print(f"[fallback] intent={intent} text={repr(text[:60])}")
    except Exception as e:
        print(f"[fallback] llm_error={e} text={repr(text[:60])}")
        return _static_fallback()

    if intent == "PLAN_TRIP":
        from bot.handlers import trip_flow
        return trip_flow.start(user_id)
    elif intent == "FIND_CHEAP":
        from bot.handlers.explore import handle_quick_explore
        from bot.handlers.settings import get_user_origin
        return handle_quick_explore(get_user_origin(user_id))
    elif intent == "PRE_TRIP":
        from bot.handlers.pre_trip import handle_pre_trip_menu
        return handle_pre_trip_menu()
    elif intent == "IDOL":
        from bot.handlers.idol_trip import handle_idol_trip
        return handle_idol_trip(text, user_id)
    elif intent == "TRANSPORT":
        from bot.handlers.transport import handle_transport
        return handle_transport(text, user_id)
    elif intent == "HOTEL":
        from bot.handlers.hotels import handle_hotels
        return handle_hotels(text, user_id)
    elif intent == "SOUVENIR":
        from bot.handlers.souvenirs import handle_souvenirs
        return handle_souvenirs(text, user_id)
    elif intent == "HELP":
        return build_help_message()
    elif intent == "UNKNOWN":
        return [{
            "type": "text",
            "text": "我是專門幫台灣人規劃出國旅遊的 Bot 🌍\n\n"
                    "這個問題我幫不上忙，但如果你有出國旅遊的需求，我很擅長！\n\n"
                    "例如：「我想去日本」「幫我找便宜的出國地點」",
            "quickReply": {"items": [
                {"type": "action", "action": {"type": "message", "label": "✨ 開始規劃旅程", "text": "開始規劃"}},
                {"type": "action", "action": {"type": "message", "label": "🌍 找便宜目的地", "text": "探索最便宜"}},
            ]},
        }]
    else:
        return _static_fallback()


def _static_fallback() -> list:
    return [{"type": "text", "text":
        "🤔 我不太確定你的意思...\n\n"
        "試試這樣輸入：\n"
        "• 「開始規劃」→ 完整旅程規劃\n"
        "• 「探索最便宜」→ 看哪裡最便宜\n"
        "• 「東京 6/15-6/20」→ 機票比價\n"
        "• 「我的追蹤」→ 查看追蹤清單\n\n"
        "輸入「使用教學」看完整說明 📖"
    }]
