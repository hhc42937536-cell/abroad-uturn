"""行前必知：簽證 + 海關 + 匯率 + 打包 — 一站式行前準備"""

import datetime
from bot.services.travel_data import get_visa_info, get_customs_info, get_packing_list
from bot.services.exchange_api import get_exchange_rate

# 熱門目的地（國家碼、旗幟、顯示名）
_POPULAR = [
    ("JP", "🇯🇵", "日本"),
    ("KR", "🇰🇷", "韓國"),
    ("TH", "🇹🇭", "泰國"),
    ("SG", "🇸🇬", "新加坡"),
    ("VN", "🇻🇳", "越南"),
    ("MY", "🇲🇾", "馬來西亞"),
    ("HK", "🇭🇰", "香港"),
    ("US", "🇺🇸", "美國"),
    ("GB", "🇬🇧", "英國"),
    ("AU", "🇦🇺", "澳洲"),
    ("FR", "🇫🇷", "法國"),
    ("ID", "🇮🇩", "印尼/峇里"),
]

# 國家名 → 國家碼
_NAME_MAP = {
    "日本": "JP", "東京": "JP", "大阪": "JP", "京都": "JP", "福岡": "JP", "沖繩": "JP", "札幌": "JP",
    "韓國": "KR", "首爾": "KR", "釜山": "KR", "濟州": "KR",
    "泰國": "TH", "曼谷": "TH", "清邁": "TH", "普吉": "TH", "普吉島": "TH",
    "新加坡": "SG",
    "越南": "VN", "胡志明": "VN", "河內": "VN",
    "馬來西亞": "MY", "吉隆坡": "MY",
    "香港": "HK",
    "澳門": "MO",
    "印尼": "ID", "峇里島": "ID", "峇里": "ID", "雅加達": "ID",
    "菲律賓": "PH", "馬尼拉": "PH",
    "美國": "US", "紐約": "US", "洛杉磯": "US",
    "英國": "GB", "倫敦": "GB",
    "法國": "FR", "巴黎": "FR",
    "德國": "DE",
    "澳洲": "AU", "雪梨": "AU", "墨爾本": "AU",
    "日本": "JP",
    "杜拜": "AE",
    "帛琉": "PW",
    "關島": "GU",
    "加拿大": "CA",
    "中國": "CN",
}

# 國家碼 → 插座/電壓資訊
_PLUG_INFO = {
    "JP": ("A 型", "100V", "台灣電器可直接使用，免帶轉接頭"),
    "KR": ("C / F 型", "220V", "需帶轉接頭；電壓與台灣不同，請確認電器標示"),
    "TH": ("A / B / C / O 型", "220V", "各飯店插座不一，建議帶萬用轉接頭"),
    "SG": ("G 型（英式）", "230V", "需帶三孔方腳轉接頭"),
    "VN": ("A / C / G 型", "220V", "各地插座混用，建議帶萬用轉接頭"),
    "MY": ("G 型（英式）", "240V", "需帶三孔方腳轉接頭"),
    "HK": ("G 型（英式）", "220V", "需帶三孔方腳轉接頭"),
    "MO": ("G 型（英式）", "220V", "需帶三孔方腳轉接頭"),
    "ID": ("C / F 型", "220V", "需帶轉接頭"),
    "PH": ("A / B 型", "220V", "插座形狀與台灣相同，但電壓較高，請確認電器標示"),
    "US": ("A / B 型", "120V", "插座形狀與台灣相同；電壓偏低，請確認電器是否支援"),
    "GB": ("G 型（英式）", "230V", "需帶三孔方腳轉接頭"),
    "FR": ("C / E 型", "230V", "需帶轉接頭"),
    "DE": ("C / F 型", "230V", "需帶轉接頭"),
    "AU": ("I 型", "230V", "與台灣相似但有差異，部分需轉接頭"),
    "AE": ("G 型（英式）", "220V", "需帶三孔方腳轉接頭"),
    "CA": ("A / B 型", "120V", "插座形狀與台灣相同；電壓偏低，請確認電器標示"),
}

# 國家碼 → 貨幣
_CURRENCY = {
    "JP": "JPY", "KR": "KRW", "TH": "THB", "SG": "SGD",
    "VN": "VND", "MY": "MYR", "HK": "HKD", "MO": "MOP",
    "ID": "IDR", "PH": "PHP", "TW": "TWD",
    "US": "USD", "GB": "GBP", "FR": "EUR", "DE": "EUR",
    "AU": "AUD", "NZ": "NZD", "CA": "CAD",
    "AE": "AED", "PW": "USD", "GU": "USD",
    "CN": "CNY", "TR": "TRY", "CH": "CHF",
}

# 國家碼 → 旗幟
_FLAG = {
    "JP": "🇯🇵", "KR": "🇰🇷", "TH": "🇹🇭", "SG": "🇸🇬",
    "VN": "🇻🇳", "MY": "🇲🇾", "HK": "🇭🇰", "MO": "🇲🇴",
    "ID": "🇮🇩", "PH": "🇵🇭", "US": "🇺🇸", "GB": "🇬🇧",
    "FR": "🇫🇷", "DE": "🇩🇪", "AU": "🇦🇺", "CA": "🇨🇦",
    "AE": "🇦🇪", "PW": "🇵🇼", "GU": "🇬🇺", "CN": "🇨🇳",
    "TR": "🇹🇷", "CH": "🇨🇭", "NZ": "🇳🇿",
}

# 國家碼 → 中文名
_NAME = {
    "JP": "日本", "KR": "韓國", "TH": "泰國", "SG": "新加坡",
    "VN": "越南", "MY": "馬來西亞", "HK": "香港", "MO": "澳門",
    "ID": "印尼", "PH": "菲律賓", "US": "美國", "GB": "英國",
    "FR": "法國", "DE": "德國", "AU": "澳洲", "CA": "加拿大",
    "AE": "阿聯酋", "PW": "帛琉", "GU": "關島", "CN": "中國",
    "TR": "土耳其", "CH": "瑞士", "NZ": "紐西蘭",
}


def handle_pre_trip_menu() -> list:
    """顯示國家快選選單"""
    buttons = []
    for cc, flag, name in _POPULAR[:8]:
        buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message",
                       "label": f"{flag} {name}",
                       "text": f"行前 {name}"},
        })

    return [
        {
            "type": "flex",
            "altText": "🛂 行前必知 — 選擇目的地",
            "contents": {
                "type": "bubble", "size": "kilo",
                "header": {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": "#1565C0", "paddingAll": "15px",
                    "contents": [
                        {"type": "text", "text": "🛂 行前必知",
                         "color": "#FFFFFF", "weight": "bold", "size": "xl"},
                        {"type": "text",
                         "text": "簽證 · 海關禁品 · 即時匯率 · 打包清單",
                         "color": "#90CAF9", "size": "xs", "margin": "xs"},
                    ],
                },
                "body": {
                    "type": "box", "layout": "vertical",
                    "spacing": "sm", "paddingAll": "12px",
                    "contents": [
                        {"type": "text", "text": "選擇目的地，一鍵整理出發前必知資訊 👇",
                         "size": "sm", "color": "#555555", "wrap": True, "margin": "xs"},
                        {"type": "separator", "margin": "sm"},
                        *buttons,
                        {"type": "button", "style": "primary", "color": "#1565C0", "height": "sm",
                         "margin": "sm",
                         "action": {"type": "message",
                                    "label": "🔍 輸入其他國家",
                                    "text": "行前必知"}},
                    ],
                },
                "footer": {
                    "type": "box", "layout": "vertical", "paddingAll": "10px",
                    "contents": [
                        {"type": "text",
                         "text": "💡 也可以直接輸入「行前 東京」「行前 泰國」",
                         "size": "xs", "color": "#888888", "align": "center", "wrap": True},
                    ],
                },
            },
        }
    ]


def handle_pre_trip_country(text: str, user_id: str = "") -> list:
    """解析目的地並回傳行前必知 Carousel"""
    clean = text.replace("行前", "").replace("必知", "").replace("行前必知", "").strip()

    if not clean:
        return handle_pre_trip_menu()

    # 解析國家碼
    cc = None
    for name, code in _NAME_MAP.items():
        if name in clean:
            cc = code
            break

    if not cc:
        # 嘗試直接輸入國家碼
        if clean.upper() in _NAME:
            cc = clean.upper()

    if not cc:
        return [
            {"type": "text",
             "text": f"找不到「{clean}」的資訊\n\n可以試試：\n"
                     "「行前 日本」「行前 韓國」「行前 泰國」「行前 美國」"},
        ] + handle_pre_trip_menu()

    flag = _FLAG.get(cc, "✈️")
    country_name = _NAME.get(cc, cc)
    currency = _CURRENCY.get(cc, "")
    month = datetime.date.today().month

    bubbles = []

    # ── Bubble 1：簽證 ──
    visa = get_visa_info(cc)
    bubbles.append(_visa_bubble(cc, flag, country_name, visa))

    # ── Bubble 2：海關禁品 ──
    customs = get_customs_info(cc)
    bubbles.append(_customs_bubble(cc, flag, country_name, customs))

    # ── Bubble 3：即時匯率 ──
    rate_info = get_exchange_rate(currency) if currency else None
    bubbles.append(_exchange_bubble(cc, flag, country_name, currency, rate_info))

    # ── Bubble 4：插座資訊 ──
    plug = _PLUG_INFO.get(cc)
    bubbles.append(_plug_bubble(cc, flag, country_name, plug))

    # ── Bubble 5：打包清單 ──
    packing = get_packing_list(cc, month)
    bubbles.append(_packing_bubble(cc, flag, country_name, packing))

    return [
        {"type": "text", "text": f"{flag} {country_name} 行前必知整理好了 👇"},
        {
            "type": "flex",
            "altText": f"{country_name} 行前必知",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


# ── 各 Bubble 建構 ────────────────────────────────────

def _visa_bubble(cc: str, flag: str, name: str, visa: dict | None) -> dict:
    if visa:
        vtype = visa.get("type", "")
        days = visa.get("days", "")
        note = visa.get("note", "")

        type_color = {
            "免簽": "#2E7D32", "落地簽": "#E65100",
            "電子簽": "#1565C0", "需要簽證": "#C62828",
        }.get(vtype, "#555555")

        body_items = [
            {"type": "text", "text": "🛂 簽證資訊",
             "weight": "bold", "size": "md", "color": "#333333"},
            {"type": "separator", "margin": "sm"},
            {"type": "box", "layout": "horizontal", "margin": "md",
             "contents": [
                 {"type": "text", "text": "類型", "size": "sm", "color": "#888888", "flex": 2},
                 {"type": "text", "text": vtype, "size": "sm", "weight": "bold",
                  "color": type_color, "flex": 4},
             ]},
        ]
        if days:
            body_items.append({
                "type": "box", "layout": "horizontal", "margin": "xs",
                "contents": [
                    {"type": "text", "text": "天數", "size": "sm", "color": "#888888", "flex": 2},
                    {"type": "text", "text": str(days), "size": "sm", "flex": 4},
                ]
            })
        if note:
            body_items += [
                {"type": "separator", "margin": "sm"},
                {"type": "text", "text": note, "size": "xs", "color": "#666666",
                 "wrap": True, "margin": "sm"},
            ]
    else:
        body_items = [
            {"type": "text", "text": "🛂 簽證資訊", "weight": "bold", "size": "md"},
            {"type": "text", "text": "建議出發前至外交部領事事務局官網確認最新簽證規定",
             "size": "sm", "color": "#666666", "wrap": True, "margin": "md"},
        ]

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1565C0", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"{flag} {name}", "color": "#FFFFFF",
                 "weight": "bold", "size": "md"},
                {"type": "text", "text": "台灣護照 · 簽證速查",
                 "color": "#90CAF9", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "xs", "paddingAll": "14px",
            "contents": body_items,
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "8px",
            "contents": [
                {"type": "button", "style": "secondary", "height": "sm",
                 "action": {"type": "uri", "label": "🔗 外交部領事局確認",
                            "uri": "https://www.boca.gov.tw/sp-foof-countrylp-01-1.html"}},
            ],
        },
    }


def _customs_bubble(cc: str, flag: str, name: str, customs: dict | None) -> dict:
    if customs:
        prohibited = customs.get("prohibited", [])
        limited = customs.get("limited", [])
        currency_limit = customs.get("currency_limit", "")

        body_items = [
            {"type": "text", "text": "🚫 海關禁帶物品",
             "weight": "bold", "size": "md", "color": "#C62828"},
            {"type": "separator", "margin": "sm"},
        ]
        for item in prohibited[:5]:
            body_items.append({
                "type": "box", "layout": "horizontal", "margin": "xs",
                "contents": [
                    {"type": "text", "text": "✗", "size": "sm", "color": "#C62828",
                     "flex": 1},
                    {"type": "text", "text": item, "size": "sm", "color": "#333333",
                     "flex": 9, "wrap": True},
                ],
            })
        if limited:
            body_items.append({
                "type": "text", "text": "⚠️ 限量攜帶",
                "weight": "bold", "size": "sm", "color": "#E65100", "margin": "md",
            })
            for item in limited[:3]:
                body_items.append({
                    "type": "text", "text": f"  · {item}", "size": "xs",
                    "color": "#666666", "wrap": True,
                })
        if currency_limit:
            body_items += [
                {"type": "separator", "margin": "sm"},
                {"type": "text", "text": f"💵 現金限額：{currency_limit}",
                 "size": "xs", "color": "#555555", "margin": "sm", "wrap": True},
            ]
    else:
        body_items = [
            {"type": "text", "text": "🚫 海關禁帶物品", "weight": "bold", "size": "md"},
            {"type": "text", "text": "請至各國海關官網查詢最新規定，帶錯物品可能被沒收或罰款",
             "size": "sm", "color": "#666666", "wrap": True, "margin": "md"},
        ]

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#B71C1C", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"{flag} {name}", "color": "#FFFFFF",
                 "weight": "bold", "size": "md"},
                {"type": "text", "text": "海關禁帶 · 限量物品",
                 "color": "#EF9A9A", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "xs", "paddingAll": "14px",
            "contents": body_items,
        },
    }


def _exchange_bubble(cc: str, flag: str, name: str,
                     currency: str, rate_info: dict | None) -> dict:
    if rate_info:
        rate = rate_info.get("rate", 0)
        display = rate_info.get("display", "")
        example = rate_info.get("example", "")

        # 常見換算
        amounts = [1000, 5000, 10000, 30000]
        rows = []
        for amt in amounts:
            converted = int(amt * rate)
            rows.append({
                "type": "box", "layout": "horizontal", "margin": "xs",
                "contents": [
                    {"type": "text", "text": f"NT$ {amt:,}",
                     "size": "sm", "color": "#555555", "flex": 4},
                    {"type": "text", "text": "→",
                     "size": "sm", "color": "#AAAAAA", "flex": 1, "align": "center"},
                    {"type": "text", "text": f"{currency} {converted:,}",
                     "size": "sm", "color": "#1565C0", "weight": "bold", "flex": 5},
                ],
            })

        body_items = [
            {"type": "text", "text": "💱 即時匯率",
             "weight": "bold", "size": "md", "color": "#1565C0"},
            {"type": "text", "text": display,
             "size": "sm", "color": "#888888", "margin": "xs"},
            {"type": "separator", "margin": "sm"},
            *rows,
        ]
    else:
        currency_display = currency or "—"
        body_items = [
            {"type": "text", "text": "💱 匯率換算",
             "weight": "bold", "size": "md"},
            {"type": "text",
             "text": f"貨幣：{currency_display}\n\n匯率資料暫時無法取得，請至銀行或 Google 查詢",
             "size": "sm", "color": "#666666", "wrap": True, "margin": "md"},
        ]

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#2E7D32", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"{flag} {name}", "color": "#FFFFFF",
                 "weight": "bold", "size": "md"},
                {"type": "text", "text": f"TWD → {currency or '?'} · 即時匯率",
                 "color": "#A5D6A7", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "xs", "paddingAll": "14px",
            "contents": body_items,
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "8px",
            "contents": [
                {"type": "text", "text": "⚠️ 僅供參考，換錢以銀行牌告匯率為準",
                 "size": "xxs", "color": "#AAAAAA", "align": "center"},
            ],
        },
    }


def _plug_bubble(cc: str, flag: str, name: str,
                 plug: tuple | None) -> dict:
    if plug:
        plug_type, voltage, tip = plug
        body_items = [
            {"type": "text", "text": "🔌 插座 & 電壓",
             "weight": "bold", "size": "md", "color": "#E65100"},
            {"type": "separator", "margin": "sm"},
            {"type": "box", "layout": "horizontal", "margin": "md",
             "contents": [
                 {"type": "text", "text": "插座型號", "size": "sm", "color": "#888888", "flex": 3},
                 {"type": "text", "text": plug_type, "size": "sm", "weight": "bold",
                  "color": "#333333", "flex": 5, "wrap": True},
             ]},
            {"type": "box", "layout": "horizontal", "margin": "xs",
             "contents": [
                 {"type": "text", "text": "電壓", "size": "sm", "color": "#888888", "flex": 3},
                 {"type": "text", "text": voltage, "size": "sm", "weight": "bold",
                  "color": "#E65100", "flex": 5},
             ]},
            {"type": "separator", "margin": "sm"},
            {"type": "text", "text": f"💡 {tip}", "size": "xs",
             "color": "#666666", "wrap": True, "margin": "sm"},
        ]
    else:
        body_items = [
            {"type": "text", "text": "🔌 插座 & 電壓", "weight": "bold", "size": "md"},
            {"type": "text",
             "text": "建議攜帶萬用轉接頭，以應對各種插座類型",
             "size": "sm", "color": "#666666", "wrap": True, "margin": "md"},
        ]

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#E65100", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"{flag} {name}", "color": "#FFFFFF",
                 "weight": "bold", "size": "md"},
                {"type": "text", "text": "插座類型 · 電壓確認",
                 "color": "#FFCCBC", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "xs", "paddingAll": "14px",
            "contents": body_items,
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "8px",
            "contents": [
                {"type": "text",
                 "text": "⚠️ 台灣電壓 110V；出國前請確認電器標示是否支援當地電壓",
                 "size": "xxs", "color": "#AAAAAA", "align": "center", "wrap": True},
            ],
        },
    }


def _packing_bubble(cc: str, flag: str, name: str, packing: dict) -> dict:
    docs = packing.get("documents", [])
    essentials = packing.get("essentials", [])
    climate_items = packing.get("climate_items", [])
    climate_label = packing.get("climate_label", "")
    country_items = packing.get("country_items", [])

    body_items = [
        {"type": "text", "text": "🧳 打包清單",
         "weight": "bold", "size": "md", "color": "#6A1B9A"},
        {"type": "separator", "margin": "sm"},
    ]

    if docs:
        body_items.append({
            "type": "text", "text": "📄 必帶證件",
            "size": "sm", "weight": "bold", "color": "#333333", "margin": "sm",
        })
        body_items.append({
            "type": "text",
            "text": "  " + "  ".join(f"✓ {d}" for d in docs[:5]),
            "size": "xs", "color": "#555555", "wrap": True,
        })

    if climate_label and climate_items:
        body_items.append({
            "type": "text", "text": f"🌡️ {climate_label} 推薦",
            "size": "sm", "weight": "bold", "color": "#333333", "margin": "sm",
        })
        body_items.append({
            "type": "text",
            "text": "  " + "  ".join(f"✓ {i}" for i in climate_items[:4]),
            "size": "xs", "color": "#555555", "wrap": True,
        })

    if country_items:
        body_items.append({
            "type": "text", "text": f"🏷️ {name} 特別建議",
            "size": "sm", "weight": "bold", "color": "#6A1B9A", "margin": "sm",
        })
        body_items.append({
            "type": "text",
            "text": "  " + "  ".join(f"✓ {i}" for i in country_items[:4]),
            "size": "xs", "color": "#555555", "wrap": True,
        })

    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#6A1B9A", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"{flag} {name}", "color": "#FFFFFF",
                 "weight": "bold", "size": "md"},
                {"type": "text", "text": "打包清單 · 按季節推薦",
                 "color": "#CE93D8", "size": "xs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "xs", "paddingAll": "14px",
            "contents": body_items if len(body_items) > 2 else [
                {"type": "text", "text": "記得帶護照、信用卡、換好外幣、充電線！",
                 "size": "sm", "color": "#666666", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "8px",
            "contents": [
                {"type": "button", "style": "primary", "color": "#6A1B9A", "height": "sm",
                 "action": {"type": "message",
                            "label": "✈️ 開始完整出國規劃",
                            "text": "開始規劃"}},
            ],
        },
    }
