"""格6：現在最夯 — 熱門玩法、體驗、必買攻略"""

import json
import os

from bot.constants.cities import IATA_TO_NAME, CITY_FLAG, IATA_TO_COUNTRY
from bot.constants.countries import COUNTRY_NAME
from bot.utils.date_parser import parse_destination


_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
_cache = {}


def _load_souvenirs() -> dict:
    if "souvenirs" in _cache:
        return _cache["souvenirs"]
    try:
        with open(os.path.join(_data_dir, "souvenirs.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["souvenirs"] = data
        return data
    except Exception as e:
        print(f"[souvenirs] Load error: {e}")
        return {}


def handle_souvenirs(text: str, user_id: str = "") -> list:
    """伴手禮 & 必買推薦入口"""
    clean = text.replace("現在最夯", "").replace("最夯", "").replace("伴手禮", "").replace("必買", "").replace("推薦", "").replace("名產", "").replace("熱門玩法", "").replace("攻略", "").strip()

    if not clean:
        return _show_trending_discovery()

    # 解析目的地
    dest_code = parse_destination(clean)
    if not dest_code:
        # 試直接用國家名
        country_map = {
            "\u65e5\u672c": "JP", "\u97d3\u570b": "KR", "\u6cf0\u570b": "TH",
            "\u65b0\u52a0\u5761": "SG", "\u8d8a\u5357": "VN",
        }
        for name, code in country_map.items():
            if name in clean:
                return _show_souvenirs(code)
        return [{"type": "text", "text":
            f"\u627e\u4e0d\u5230\u300c{clean}\u300d\u7684\u4f34\u624b\u79ae\u8cc7\u8a0a\n\n"
            f"\u76ee\u524d\u652f\u63f4\uff1a\u65e5\u672c\u3001\u97d3\u570b\u3001\u6cf0\u570b\u3001\u65b0\u52a0\u5761\u3001\u8d8a\u5357"}]

    country = IATA_TO_COUNTRY.get(dest_code, "")
    if not country:
        return [{"type": "text", "text": f"\u627e\u4e0d\u5230\u9019\u500b\u76ee\u7684\u5730\u7684\u4f34\u624b\u79ae\u8cc7\u8a0a"}]

    return _show_souvenirs(country)


def _show_souvenirs(country_code: str) -> list:
    """顯示指定國家的伴手禮推薦（靜態資料 + 即時爬蟲）"""
    data = _load_souvenirs()
    info = data.get(country_code)

    if not info:
        country_name = COUNTRY_NAME.get(country_code, country_code)
        return [{"type": "text", "text":
            f"\u76ee\u524d\u9084\u6c92\u6709 {country_name} \u7684\u4f34\u624b\u79ae\u8cc7\u8a0a\uff0c\u6211\u5011\u6703\u76e1\u5feb\u65b0\u589e\uff01"}]

    country_name = info.get("country_name", country_code)
    must_buy = info.get("must_buy", [])
    shops = info.get("shopping_areas", [])
    tax_tip = info.get("tax_free_tip", "")

    bubbles = []

    # Bubble 1: 必買清單
    buy_contents = []
    for item in must_buy[:8]:
        buy_contents.append({
            "type": "box", "layout": "vertical", "margin": "sm",
            "contents": [
                {"type": "text", "text": f"\U0001f381 {item['name']}",
                 "size": "sm", "weight": "bold", "color": "#333333", "wrap": True},
                {"type": "text",
                 "text": f"  {item.get('category','')}  {item.get('price_range','')}  \U0001f4cd{item.get('where','')}",
                 "size": "xxs", "color": "#888888", "wrap": True},
            ],
        })

    bubbles.append({
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#FF6B35", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"\U0001f381 {country_name} \u7d93\u5178\u5fc5\u8cb7",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
                {"type": "text", "text": "\u85e5\u599d\u3001\u7f8e\u599d\u3001\u5c0f\u5bb6\u96fb\u3001\u98df\u54c1\u3001\u9ad4\u9a57\u5168\u5305",
                 "color": "#FFFFFF99", "size": "xxs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "10px", "spacing": "xs",
            "contents": buy_contents,
        },
    })

    # Bubble 2: 熱門體驗（靜態資料）
    hot_exp = info.get("hot_experiences", [])
    if hot_exp:
        exp_lines = []
        for exp in hot_exp[:5]:
            name = exp.get("name", "")
            tip = exp.get("tip", "")
            exp_lines.append(f"\U0001f525 {name}")
            if tip:
                exp_lines.append(f"   \U0001f4a1 {tip}")
            exp_lines.append("")
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#9C27B0", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": f"\U0001f3ab {country_name} \u8d85\u71b1\u9580\u9ad4\u9a57",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "\u9019\u4e9b\u884c\u7a0b\u8d85\u591a\u4eba\u63a8\u85a6\uff01",
                     "color": "#FFFFFF99", "size": "xxs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\n".join(exp_lines).strip(),
                     "size": "sm", "color": "#444444", "wrap": True},
                ],
            },
        })

    # Bubble 3: 韓國醫美（只有 KR）
    med = info.get("medical_beauty", {})
    if med:
        treat_lines = []
        for t in med.get("popular_treatments", [])[:4]:
            treat_lines.append(f"\U0001f489 {t['name']}")
            treat_lines.append(f"   \U0001f4b0 {t.get('price','')}  \U0001f4a1 {t.get('tip','')}")
            treat_lines.append("")
        warn = med.get("warning", "")
        if warn:
            treat_lines.append(warn)
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E63", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f48a \u97d3\u570b\u91ab\u7f8e\u6307\u5357",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "\u6bd4\u53f0\u7063\u4fbf\u5b9c 3-5 \u6298\uff0c\u5f88\u591a\u4eba\u5c08\u7a0b\u4f86\u505a",
                     "color": "#FFFFFF99", "size": "xxs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\n".join(treat_lines).strip(),
                     "size": "sm", "color": "#444444", "wrap": True},
                ],
            },
        })

    # Bubble 4: KKday/Klook 即時熱門活動（只用快取，避免 Vercel 超時）
    try:
        from bot.services.trending import scrape_kkday_hot, scrape_klook_hot
        kkday_items = scrape_kkday_hot(country_code, cache_only=True)
        if kkday_items:
            lines = [f"{i+1}. {it['title'][:35]}" + (f"\n   💰{it['price']}" if it.get('price') else "")
                     for i, it in enumerate(kkday_items[:6])]
            bubbles.append({
                "type": "bubble", "size": "kilo",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#00897B", "paddingAll": "12px",
                    "contents": [
                        {"type": "text", "text": "\U0001f3ab KKday \u71b1\u9580\u6d3b\u52d5",
                         "color": "#FFFFFF", "weight": "bold", "size": "md"},
                        {"type": "text", "text": "\u5373\u6642\u722c\u53d6 \u2022 \u6bcf\u65e5\u66f4\u65b0",
                         "color": "#FFFFFF99", "size": "xxs"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical", "paddingAll": "12px",
                    "contents": [
                        {"type": "text", "text": "\n".join(lines),
                         "size": "sm", "color": "#444444", "wrap": True},
                    ],
                },
            })
    except Exception as e:
        print(f"[souvenirs] kkday/klook error: {e}")

    # Bubble 5: 即時美妝/商品排行（Cosme/OliveYoung 爬蟲）
    try:
        from bot.services.trending import get_trending_souvenirs
        trending = get_trending_souvenirs(country_code, cache_only=True)
        for source in trending.get("sources", [])[:1]:
            source_name = source.get("name", "")
            items = source.get("items", [])
            if not items:
                continue
            lines = []
            for i, item in enumerate(items[:6]):
                name_str = item.get("name", item.get("title", ""))[:35]
                lines.append(f"{i+1}. {name_str}")
                if item.get("price"):
                    lines.append(f"   \U0001f4b0 {item['price']}")
            if lines:
                bubbles.append({
                    "type": "bubble", "size": "kilo",
                    "header": {
                        "type": "box", "layout": "vertical",
                        "backgroundColor": "#E91E63", "paddingAll": "12px",
                        "contents": [
                            {"type": "text", "text": f"\U0001f525 {source_name} \u71b1\u9580\u6392\u884c",
                             "color": "#FFFFFF", "weight": "bold", "size": "md"},
                            {"type": "text", "text": "\u5373\u6642\u722c\u53d6 \u2022 \u6bcf\u65e5\u66f4\u65b0",
                             "color": "#FFFFFF99", "size": "xxs"},
                        ],
                    },
                    "body": {
                        "type": "box", "layout": "vertical", "paddingAll": "12px",
                        "contents": [
                            {"type": "text", "text": "\n".join(lines),
                             "size": "sm", "color": "#444444", "wrap": True},
                        ],
                    },
                })
    except Exception as e:
        print(f"[souvenirs] trending error: {e}")

    # Bubble 6: 購物地點 + 退稅
    if shops:
        shop_lines = []
        for shop in shops[:4]:
            shop_lines.append(f"\U0001f6cd\ufe0f {shop['name']}（{shop.get('type', '')}）")
            shop_lines.append(f"   \U0001f4a1 {shop.get('tip', '')}")
            shop_lines.append("")
        if tax_tip:
            shop_lines.append(f"\U0001f4b0 \u9000\u7a05\uff1a{tax_tip}")
        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#2E7D32", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": f"\U0001f6cd\ufe0f {country_name} \u8cfc\u7269\u5730\u9ede & \u9000\u7a05",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\n".join(shop_lines).strip(),
                     "size": "sm", "color": "#444444", "wrap": True},
                ],
            },
        })

    return [
        {"type": "text", "text": f"\U0001f525 {country_name} \u73fe\u5728\u6700夯\uff01\u71b1\u9580\u9ad4\u9a57 & \u5fc5\u8cb7\u6e05\u55ae\n\u2190 \u5de6\u53f3\u6ed1\u52d5\u67e5\u770b"},
        {
            "type": "flex",
            "altText": f"\U0001f525 {country_name} \u73fe\u5728\u6700夯",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def _show_trending_discovery() -> list:
    """入口：展示各國現在最夯的玩法、體驗、必買亮點"""
    data = _load_souvenirs()

    countries = [
        ("JP", "\U0001f1ef\U0001f1f5", "#C62828", "\u85e5\u599d\u4e09\u672c\u67f1\u30fb\u5c0f\u5bb6\u96fb\u30fb\u96fb\u5668\u5929\u5802"),
        ("KR", "\U0001f1f0\U0001f1f7", "#1565C0", "\u91ab\u7f8e\u30fb\u62cd\u8cbc\u6a5f\u30fb Olive Young"),
        ("TH", "\U0001f1f9\U0001f1ed", "#AD1457", "\u9435\u9053\u5e02\u5834\u30fb\u53e4\u6cd5\u6309\u6469\u30fb\u5920\u5e02"),
        ("SG", "\U0001f1f8\U0001f1ec", "#2E7D32", "\u74b0\u7403\u5f71\u57ce\u30fb\u6fd1\u6d77\u7063\u82b1\u5712\u30fb C&K \u5305\u5305"),
        ("VN", "\U0001f1fb\U0001f1f3", "#E65100", "\u53e4\u82b8\u5730\u9053\u30fb\u6e7f\u516c\u6cb3\u904a\u8239\u30fb\u5967\u9edb\u8a02\u88fd"),
    ]

    bubbles = []
    for code, flag, color, tagline in countries:
        info = data.get(code, {})
        if not info:
            continue
        country_name = info.get("country_name", code)
        hot_exp = info.get("hot_experiences", [])
        must_buy = info.get("must_buy", [])
        med = info.get("medical_beauty", {})

        body_items = []

        # 1. 熱門體驗（最多 3 項，優先展示）
        for exp in hot_exp[:3]:
            body_items.append({
                "type": "box", "layout": "horizontal", "margin": "sm", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "\U0001f525", "size": "sm", "flex": 1},
                    {"type": "text", "text": exp["name"],
                     "size": "sm", "weight": "bold", "color": "#222222", "flex": 9, "wrap": True},
                ]
            })

        # 2. 韓國醫美特別區
        if med and code == "KR":
            treatments = med.get("popular_treatments", [])[:2]
            if treatments:
                body_items.append({"type": "separator", "margin": "sm"})
                body_items.append({
                    "type": "text", "text": "\U0001f489 \u97d3\u570b\u91ab\u7f8e\u8d85\u71b1\uff01\u6bd4\u53f0\u7063\u4fbf\u5b9c 3-5 \u6298",
                    "size": "xs", "color": "#C62828", "weight": "bold", "margin": "sm", "wrap": True,
                })
                for t in treatments:
                    body_items.append({
                        "type": "text",
                        "text": f"  \u2022 {t['name']}  {t.get('price','')}",
                        "size": "xs", "color": "#555555", "wrap": True,
                    })

        # 3. 必買亮點（若熱門體驗不足則補充，共最多 5 行）
        remaining = max(0, 4 - len(hot_exp[:3]))
        for item in must_buy[:remaining]:
            body_items.append({
                "type": "box", "layout": "horizontal", "margin": "xs", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": "\U0001f6cd\ufe0f", "size": "sm", "flex": 1},
                    {"type": "text", "text": item["name"],
                     "size": "sm", "color": "#444444", "flex": 9, "wrap": True},
                ]
            })

        # KKday 即時熱門（若有快取）
        kkday_preview = []
        try:
            from bot.services.trending import scrape_kkday_hot
            items = scrape_kkday_hot(code, limit=2, cache_only=True)
            if items:
                body_items.append({"type": "separator", "margin": "sm"})
                body_items.append({
                    "type": "text", "text": "\U0001f3ab KKday \u71b1\u9580",
                    "size": "xs", "color": "#00897B", "weight": "bold", "margin": "xs",
                })
                for it in items:
                    body_items.append({
                        "type": "text", "text": f"  \u2022 {it['title'][:28]}",
                        "size": "xs", "color": "#555555", "wrap": True,
                    })
        except Exception:
            pass

        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": color, "paddingAll": "14px",
                "contents": [
                    {"type": "text", "text": f"{flag} {country_name}",
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": tagline,
                     "color": "#FFFFFF99", "size": "xs", "margin": "xs", "wrap": True},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "xs", "paddingAll": "12px",
                "contents": body_items if body_items else [
                    {"type": "text", "text": "\u6b63\u5728\u66f4\u65b0\u4e2d\u2026",
                     "size": "sm", "color": "#999999"}
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical", "paddingAll": "10px",
                "contents": [
                    {"type": "button", "style": "primary", "color": color, "height": "sm",
                     "action": {"type": "message",
                                "label": f"\U0001f4cd {country_name} \u5b8c\u6574\u653b\u7565",
                                "text": f"\u73fe\u5728\u6700夯 {country_name}"}},
                ],
            },
        })

    quick_reply_items = [
        {"type": "action", "action": {"type": "message", "label": "\U0001f1ef\U0001f1f5 \u65e5\u672c", "text": "\u73fe\u5728\u6700夯 \u65e5\u672c"}},
        {"type": "action", "action": {"type": "message", "label": "\U0001f1f0\U0001f1f7 \u97d3\u570b", "text": "\u73fe\u5728\u6700夯 \u97d3\u570b"}},
        {"type": "action", "action": {"type": "message", "label": "\U0001f1f9\U0001f1ed \u6cf0\u570b", "text": "\u73fe\u5728\u6700夯 \u6cf0\u570b"}},
        {"type": "action", "action": {"type": "message", "label": "\U0001f1f8\U0001f1ec \u65b0\u52a0\u5761", "text": "\u73fe\u5728\u6700夯 \u65b0\u52a0\u5761"}},
        {"type": "action", "action": {"type": "message", "label": "\U0001f1fb\U0001f1f3 \u8d8a\u5357", "text": "\u73fe\u5728\u6700夯 \u8d8a\u5357"}},
    ]

    return [
        {"type": "text",
         "text": "\U0001f525 \u73fe\u5728\u6700夯\uff01\n\u5404\u570b\u6700\u71b1\u73a9\u6cd5\u3001\u9ad4\u9a57\u3001\u5fc5\u8cb7\u4e00\u6b21\u770b\u6e05\n\u2190 \u5de6\u53f3\u6ed1\u52d5\uff0c\u9ede\u300c\u5b8c\u6574\u653b\u7565\u300d\u770b\u8a73\u7d30"},
        {
            "type": "flex",
            "altText": "\U0001f525 \u5404\u570b\u73fe\u5728\u6700夯",
            "contents": {"type": "carousel", "contents": bubbles},
            "quickReply": {"items": quick_reply_items},
        },
    ]
