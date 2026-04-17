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
        if step > 0:
            return trip_flow._show_step_prompt(user_id, step)
        return [{"type": "text", "text": "\u4f60\u76ee\u524d\u6c92\u6709\u9032\u884c\u4e2d\u7684\u898f\u5283\u3002\u8f38\u5165\u300c\u958b\u59cb\u898f\u5283\u300d\u958b\u59cb\u5427\uff01"}]

    # ── 出發地設定 ──
    if "出發地" in text or text in ("設定出發地", "出發機場", "改出發地"):
        from bot.handlers.settings import handle_set_origin
        return handle_set_origin(user_id, text)

    # ── Rich Menu 固定功能（永遠優先，不被 session 攔截）──
    if text in ("\u8aaa\u8d70\u5c31\u8d70", "\u8aaa\u8d70\u5c31\u98db", "\u99ac\u4e0a\u98db", "\u5feb\u901f\u898f\u5283"):
        from bot.handlers.quick_trip import handle_quick_trip
        return handle_quick_trip(user_id, text)

    if text in ("\u958b\u59cb\u898f\u5283", "\u5b8c\u6574\u51fa\u570b\u898f\u5283", "\u898f\u5283\u65c5\u7a0b"):
        return trip_flow.start(user_id)

    if any(kw in text for kw in ("\u73fe\u5728\u6700\u5938", "\u6700\u5938", "\u4f34\u624b\u79ae", "\u5fc5\u8cb7", "\u71b1\u9580\u73a9\u6cd5")):
        from bot.handlers.souvenirs import handle_souvenirs
        return handle_souvenirs(text, user_id)

    if "\u8ffd\u661f" in text:
        from bot.handlers.idol_trip import handle_idol_trip
        return handle_idol_trip(text, user_id)

    if text in ("\u4ea4\u901a\u653b\u7565", "\u4ea4\u901a") or any(kw in text for kw in ("\u4ea4\u901a\u653b\u7565", "\u4ea4\u901a\u5361", "\u5730\u9435\u5361", "\u897f\u74dc\u5361", "\u516b\u9054\u901a", "T-money", "Suica", "EZ-Link", "Octopus", "\u5154\u5b50\u5361")):
        from bot.handlers.transport import handle_transport
        return handle_transport(text, user_id)

    if text in ("\u6211\u7684\u65c5\u884c\u8a08\u756b", "\u6211\u7684\u8a08\u756b", "\u65c5\u884c\u8a08\u756b"):
        from bot.handlers.my_plans import handle_my_plans
        return handle_my_plans(user_id)

    if text in ("\u4f4f\u5bbf", "\u4f4f\u5bbf\u63a8\u85a6") or ("\u4f4f\u5bbf" in text and len(text) <= 6):
        from bot.handlers.hotels import handle_hotels
        return handle_hotels(text, user_id)

    if text in ("\u8a2d\u5b9a",):
        current = get_user_origin(user_id)
        name_map = {"TPE": "\u53f0\u5317\u6241\u5712", "KHH": "\u9ad8\u96c4\u5c0f\u6e2f", "RMQ": "\u53f0\u4e2d\u6e05\u6cc9\u5c97", "TNN": "\u53f0\u5357"}
        current_name = name_map.get(current, current)
        return [{
            "type": "flex",
            "altText": "\u2699\ufe0f \u8a2d\u5b9a",
            "contents": {
                "type": "bubble", "size": "kilo",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#37474F", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "\u2699\ufe0f \u8a2d\u5b9a",
                         "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                        {"type": "text", "text": f"\u51fa\u767c\u5730\uff1a{current_name} ({current})",
                         "color": "#B0BEC5", "size": "sm"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "15px",
                    "contents": [
                        {"type": "button", "style": "primary", "color": "#FF6B35", "height": "sm",
                         "action": {"type": "message", "label": "\u2708\ufe0f \u8b8a\u66f4\u51fa\u767c\u5730", "text": "\u51fa\u767c\u5730"}},
                        {"type": "button", "style": "secondary", "height": "sm",
                         "action": {"type": "message", "label": "\U0001f4d6 \u4f7f\u7528\u8aaa\u660e", "text": "\u4f7f\u7528\u8aaa\u660e"}},
                    ],
                },
            },
        }]

    if text in ("\u4f7f\u7528\u8aaa\u660e", "\u8aaa\u660e", "\u4f7f\u7528\u6559\u5b78", "\u5e6b\u52a9", "help"):
        return build_help_message()

    # ── 2. 檢查是否有進行中的規劃 session ──
    step = get_step(user_id)
    if step > 0:
        # 在規劃流程中，處理預算相關輸入
        session = get_session(user_id) or {}
        if step == 3 and session.get("adults") and not session.get("budget"):
            # 已輸入人數但還沒輸入預算 → 所有輸入都當作預算
            return trip_flow._prompt_budget_response(user_id, text)

        return trip_flow.handle_step(user_id, text, step)

    # ── 3. 無 session → 進入規劃或獨立功能 ──
    if text in ("開始規劃", "我要規劃旅行", "完整出國規劃", "規劃旅程", "旅行規劃"):
        return trip_flow.start(user_id)

    # ── 說走就走（極速模式）──
    if text in ("說走就走", "說走就飛", "馬上飛", "快速規劃"):
        from bot.handlers.quick_trip import handle_quick_trip
        return handle_quick_trip(user_id, text)

    # ── 快速探索 ──
    from bot.handlers.explore import (
        handle_quick_explore, handle_explore, handle_compare,
        handle_direct_flights, handle_transfer_cheapest,
        handle_flexible_dates, handle_package, handle_popular_countries,
    )
    from bot.flex.month_picker import month_picker_flex

    if text in ("便宜", "最便宜", "探索", "便宜國外探索"):
        return handle_quick_explore(origin)

    if text in ("探索最便宜", "便宜探索"):
        from bot.handlers.explore import handle_explore_cheapest
        return handle_explore_cheapest(origin)

    if text in ("選月份",):
        return month_picker_flex()

    if text.startswith("探索|"):
        parts = text.split("|")
        if len(parts) >= 2:
            return handle_explore(parts[1], origin)

    # ── 簽證速查（文字觸發，不在 Rich Menu）──
    from bot.handlers.visa import handle_visa
    if any(kw in text for kw in ("\u7c3d\u8b49", "\u9700\u8981\u7c3d\u8b49", "\u514d\u7c3d", "\u843d\u5730\u7c3d", "\u96fb\u5b50\u7c3d", "\u7c3d\u8b49\u67e5\u8a62", "\u7c3d\u8b49\u901f\u67e5")):
        return handle_visa(text, user_id)

    # ── 當地交通攻略（格4）──
    from bot.handlers.transport import handle_transport
    if text in ("\u4ea4\u901a\u653b\u7565", "\u4ea4\u901a") or any(kw in text for kw in ("\u4ea4\u901a\u653b\u7565", "\u4ea4\u901a\u5361", "\u5730\u9435\u5361", "\u767c\u5361", "\u897f\u74dc\u5361", "\u516b\u9054\u901a", "T-money", "Suica", "EZ-Link", "Octopus", "\u5154\u5b50\u5361")):
        return handle_transport(text, user_id)

    # ── 行前必知（格6，取代我的旅行計畫）──
    if text in ("行前必知", "行前準備", "出發準備", "簽證匯率"):
        from bot.handlers.pre_trip import handle_pre_trip_menu
        return handle_pre_trip_menu()

    if text.startswith("行前 ") or text.startswith("行前|"):
        from bot.handlers.pre_trip import handle_pre_trip_country
        return handle_pre_trip_country(text, user_id)

    # ── 我的旅行計畫（保留文字觸發，Rich Menu 已移除）──
    from bot.handlers.my_plans import handle_my_plans
    if text in ("我的旅行計畫", "我的計畫", "旅行計畫"):
        return handle_my_plans(user_id)

    # ── 住宿推薦（格5）──
    from bot.handlers.hotels import handle_hotels
    if "住宿" in text or "飯店" in text:
        return handle_hotels(text, user_id)

    # ── 現在最夯 / 伴手禮（格6）──
    from bot.handlers.souvenirs import handle_souvenirs
    if any(kw in text for kw in ("現在最夯", "最夯", "伴手禮", "必買", "名產", "熱門玩法")):
        return handle_souvenirs(text, user_id)

    # ── 追星（格7）──
    from bot.handlers.idol_trip import handle_idol_trip
    if "追星" in text:
        return handle_idol_trip(text, user_id)

    # ── 價格追蹤 ──
    from bot.handlers.tracking import handle_track, handle_cancel_track, handle_my_tracks

    if text.startswith("追蹤|"):
        return handle_track(user_id, text)

    if text.startswith("取消追蹤"):
        return handle_cancel_track(user_id, text)

    if text in ("我的追蹤", "追蹤清單", "價格追蹤"):
        return handle_my_tracks(user_id)

    # ── 使用教學 ──
    if text in ("使用教學", "使用說明", "幫助", "說明", "help"):
        return build_help_message()

    # ── 智慧偵測：城市名 + 日期 → 自動比價 ──
    from bot.utils.date_parser import parse_destination, parse_date_range
    from bot.constants.cities import IATA_TO_NAME

    dest = parse_destination(text)
    if dest:
        depart, ret = parse_date_range(text)
        if depart:
            return handle_compare(text, origin)
        else:
            # 有目的地但無日期 → 直接啟動規劃 session，下一句就能接日期
            return trip_flow.start_with_destination(user_id, text)

    # ── 旅行工具箱 ──
    if text in ("旅行工具", "工具箱", "工具", "設定"):
        return _build_toolbox()

    # ── 彈性日期 ──
    if "彈性日期" in text or text == "彈性":
        return handle_flexible_dates(text.replace("彈性日期", "").replace("彈性", "").strip(), origin)

    # ── 直飛 ──
    if text in ("直飛", "直飛優先", "只要直飛"):
        return handle_direct_flights(origin)

    # ── 轉機最省 ──
    if text in ("轉機", "轉機最省", "最省轉機"):
        return handle_transfer_cheapest(origin)

    # ── 機加酒 ──
    if "機加酒" in text:
        return handle_package(text.replace("機加酒", "").strip(), origin)

    # ── 熱門國家 ──
    if "熱門國家" in text or text in ("熱門", "熱門目的地", "國家"):
        return handle_popular_countries(origin)

    # ── Fallback ──
    return [{"type": "text", "text":
        "\U0001f914 \u6211\u4e0d\u592a\u78ba\u5b9a\u4f60\u7684\u610f\u601d...\n\n"
        "\u8a66\u8a66\u9019\u6a23\u8f38\u5165\uff1a\n"
        "\u2022 \u300c\u958b\u59cb\u898f\u5283\u300d \u2192 \u5b8c\u6574\u65c5\u7a0b\u898f\u5283\n"
        "\u2022 \u300c\u63a2\u7d22\u6700\u4fbf\u5b9c\u300d \u2192 \u770b\u54ea\u88e1\u6700\u4fbf\u5b9c\n"
        "\u2022 \u300c\u6771\u4eac 6/15-6/20\u300d \u2192 \u6a5f\u7968\u6bd4\u50f9\n"
        "\u2022 \u300c\u6211\u7684\u8ffd\u8e64\u300d \u2192 \u67e5\u770b\u8ffd\u8e64\u6e05\u55ae\n\n"
        "\u8f38\u5165\u300c\u4f7f\u7528\u6559\u5b78\u300d\u770b\u5b8c\u6574\u8aaa\u660e \U0001f4d6"
    }]


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
