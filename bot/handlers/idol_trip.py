"""格7：追星行程規劃"""

import json
import os

from bot.constants.cities import IATA_TO_NAME, CITY_FLAG, CITY_CODES
from bot.services.scraper import scrape_idol_events
from bot.services.redis_store import redis_get, redis_set

_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
_cache = {}


def _load_idol_data() -> dict:
    if "idol" in _cache:
        return _cache["idol"]
    try:
        with open(os.path.join(_data_dir, "idol_events.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache["idol"] = data
        return data
    except Exception as e:
        print(f"[idol] Load error: {e}")
        return {}


def handle_idol_trip(text: str, user_id: str = "") -> list:
    """追星行程規劃入口"""
    clean = text.replace("追星", "").replace("行程", "").replace("規劃", "").strip()

    if not clean:
        return _show_idol_menu()

    data = _load_idol_data()

    # 1. 搜尋歌手/團體
    all_groups = []
    for cc, groups in data.get("groups", {}).items():
        for g in groups:
            all_groups.append((g, cc))

    for group, cc in all_groups:
        if clean.lower() in group["name"].lower() or group["name"].lower() in clean.lower():
            return _show_artist_info(group, data, country=cc, is_actor=False)

    # 2. 搜尋演員
    all_actors = []
    for cc, actors in data.get("actors", {}).items():
        for a in actors:
            all_actors.append((a, cc))

    for actor, cc in all_actors:
        if clean.lower() in actor["name"].lower() or actor["name"].lower() in clean.lower():
            return _show_artist_info(actor, data, country=cc, is_actor=True)

    # 3. 沒匹配到，嘗試爬蟲搜尋
    events = scrape_idol_events(clean)
    if events:
        return _show_scraped_events(clean, events)

    return [{
        "type": "text",
        "text": f"找不到「{clean}」的相關活動資訊\n\n可以試試：\n「追星 邊佑錫」「追星 BTS」「追星 Snow Man」",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "message", "label": "邊佑錫", "text": "追星 邊佑錫"}},
                {"type": "action", "action": {"type": "message", "label": "BTS", "text": "追星 BTS"}},
                {"type": "action", "action": {"type": "message", "label": "BLACKPINK", "text": "追星 BLACKPINK"}},
                {"type": "action", "action": {"type": "message", "label": "乃木坂46", "text": "追星 乃木坂46"}},
                {"type": "action", "action": {"type": "message", "label": "Snow Man", "text": "追星 Snow Man"}},
            ],
        },
    }]


def _show_idol_menu() -> list:
    """顯示追星首頁選單（先種草 → 再選藝人）"""
    data = _load_idol_data()
    tips = data.get("tips", [])

    # ── K-POP bubble ──
    kr_groups = data.get("groups", {}).get("KR", [])
    kr_buttons = []
    for g in kr_groups[:6]:
        kr_buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": g["name"][:12], "text": f"\u8ffd\u661f {g['name']}"},
        })
    # K-POP 介紹區
    kr_intro = [
        {"type": "text",
         "text": "\U0001f3ab \u6f14\u5531\u6703 \u30fb \u898f\u5283 \u30fb \u5468\u908a\u5546\u5e97",
         "size": "xs", "color": "#FFFFFF99", "margin": "xs"},
    ]

    # ── J-POP：偶像 / 歌手 分類 ──
    jp_groups = data.get("groups", {}).get("JP", [])
    jp_idols = [g for g in jp_groups if g.get("category") == "偶像"]
    jp_singers = [g for g in jp_groups if g.get("category") == "歌手"]

    jp_idol_buttons = []
    for g in jp_idols[:6]:
        jp_idol_buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": g["name"][:12], "text": f"追星 {g['name']}"},
        })

    jp_singer_buttons = []
    for g in jp_singers[:6]:
        jp_singer_buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": g["name"][:12], "text": f"追星 {g['name']}"},
        })

    # ── 日本演員 bubble ──
    jp_actors = data.get("actors", {}).get("JP", [])
    jp_male_actors = [a for a in jp_actors if "女" not in a.get("type", "")]
    jp_female_actors = [a for a in jp_actors if "女" in a.get("type", "")]
    jp_pick = jp_male_actors[:3] + jp_female_actors[:3]
    if len(jp_pick) < 6:
        jp_pick += [a for a in jp_actors if a not in jp_pick][:6 - len(jp_pick)]
    jp_actor_buttons = []
    for a in jp_pick:
        jp_actor_buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": a["name"][:12], "text": f"追星 {a['name']}"},
        })

    # ── 韓劇演員 bubble：男女各 3，避免全男星 ──
    kr_actors = data.get("actors", {}).get("KR", [])
    male_actors = [a for a in kr_actors if a.get("type", "") in ("演員", "演員/偶像")]
    female_actors = [a for a in kr_actors if "女" in a.get("type", "")]
    # 男 3 女 3，不足補對方
    pick = male_actors[:3] + female_actors[:3]
    if len(pick) < 6:
        pick += [a for a in kr_actors if a not in pick][:6 - len(pick)]
    actor_buttons = []
    for a in pick:
        actor_buttons.append({
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": a["name"][:8], "text": f"追星 {a['name']}"},
        })

    # ── 追星小知識 bubble ──
    tip_lines = []
    for t in tips[:4]:
        tip_lines.append({
            "type": "box", "layout": "horizontal", "margin": "sm",
            "contents": [
                {"type": "text", "text": "\U0001f4a1", "size": "sm", "flex": 1},
                {"type": "text", "text": t, "size": "xs", "color": "#555555",
                 "flex": 11, "wrap": True},
            ],
        })

    bubbles = [
        # K-POP
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E91E63", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "🇰🇷 K-POP 韓國偶像",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "點選你喜歡的團體",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": kr_buttons,
            },
        },
        # 韓劇演員
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#1A237E", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "🎬 韓劇／韓星 演員",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "粉絲見面會・來台活動・男女星皆有",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": actor_buttons if actor_buttons else [
                    {"type": "text", "text": "輸入「追星 邊佑錫」查詢",
                     "size": "sm", "color": "#888888"},
                ],
            },
        },
        # J-POP 偶像
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#E64A19", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "🇯🇵 日本偶像",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "Johnny's・坂道系・BE:FIRST",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": jp_idol_buttons if jp_idol_buttons else [
                    {"type": "text", "text": "輸入「追星 Snow Man」查詢",
                     "size": "sm", "color": "#888888"},
                ],
            },
        },
        # 日本歌手/樂團
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#37474F", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "🎵 日本歌手／樂團",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "YOASOBI・Ado・米津玄師・King Gnu",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": jp_singer_buttons if jp_singer_buttons else [
                    {"type": "text", "text": "輸入「追星 YOASOBI」查詢",
                     "size": "sm", "color": "#888888"},
                ],
            },
        },
        # 日本影視演員
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#880E4F", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "🎬 日本影視演員",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "男女星皆有・舞台・見面會",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "sm", "paddingAll": "12px",
                "contents": jp_actor_buttons if jp_actor_buttons else [
                    {"type": "text", "text": "輸入「追星 新垣結衣」查詢",
                     "size": "sm", "color": "#888888"},
                ],
            },
        },
        # 追星小知識
        {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#6A1B9A", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f4a1 \u8ffd\u661f\u5c0f\u77e5\u8b58",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "\u51fa\u767c\u524d\u5fc5\u9808\u77e5\u9053\u7684\u4e8b",
                     "color": "#FFFFFF88", "size": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "spacing": "xs", "paddingAll": "12px",
                "contents": tip_lines if tip_lines else [
                    {"type": "text", "text": "\u62b1\u6b49\uff0c\u76ee\u524d\u6c92\u6709\u8cc7\u6599",
                     "size": "sm", "color": "#888888"},
                ],
            },
        },
        # 搜尋其他
        {
            "type": "bubble", "size": "kilo",
            "body": {
                "type": "box", "layout": "vertical",
                "justifyContent": "center", "alignItems": "center",
                "paddingAll": "20px", "spacing": "md",
                "contents": [
                    {"type": "text", "text": "\U0001f50d", "size": "3xl", "align": "center"},
                    {"type": "text", "text": "\u641c\u5c0b\u5176\u4ed6\u85dd\u4eba",
                     "weight": "bold", "size": "md", "align": "center"},
                    {"type": "text",
                     "text": "\u76f4\u63a5\u8f38\u5165\u85dd\u4eba\u540d\u7a31\uff0c\u4f8b\u5982\uff1a\n\u300c\u8ffd\u661f IVE\u300d",
                     "size": "sm", "color": "#888888", "align": "center", "wrap": True},
                ],
            },
        },
    ]

    return [
        {
            "type": "flex",
            "altText": "\u2b50 \u8ffd\u661f\u884c\u7a0b\u898f\u5283",
            "contents": {"type": "carousel", "contents": bubbles},
            "quickReply": {
                "items": [
                    {"type": "action", "action": {"type": "message", "label": "BTS", "text": "\u8ffd\u661f BTS"}},
                    {"type": "action", "action": {"type": "message", "label": "BLACKPINK", "text": "\u8ffd\u661f BLACKPINK"}},
                    {"type": "action", "action": {"type": "message", "label": "TWICE", "text": "\u8ffd\u661f TWICE"}},
                    {"type": "action", "action": {"type": "message", "label": "aespa", "text": "\u8ffd\u661f aespa"}},
                    {"type": "action", "action": {"type": "message", "label": "\u4e43\u672946", "text": "\u8ffd\u661f \u4e43\u672946"}},
                    {"type": "action", "action": {"type": "message", "label": "Snow Man", "text": "\u8ffd\u661f Snow Man"}},
                ],
            },
        },
    ]


def _show_artist_info(artist: dict, data: dict, country: str = "", is_actor: bool = False) -> list:
    """顯示藝人/演員資訊 + 近期活動 + 周邊商店"""
    name = artist["name"]
    agency = artist.get("agency", "")

    bubbles = []

    # Bubble 1: 資訊卡
    if is_actor:
        known_for = artist.get("known_for", "")
        body_text = f"🎬 {known_for}\n🏢 {agency}" if known_for else f"🏢 {agency}"
        header_color = "#1A237E"
        header_icon = "🎬"
    else:
        genre = artist.get("genre", "")
        body_text = f"\U0001f3e2 {agency}\n\U0001f3b6 {genre}"
        header_color = "#E91E63"
        header_icon = "⭐"
    bubbles.append({
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_color, "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"{header_icon} {name}",
                 "color": "#FFFFFF", "weight": "bold", "size": "lg"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": body_text, "size": "sm", "color": "#444444", "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "10px",
            "contents": [
                {"type": "button", "style": "primary", "color": header_color, "height": "sm",
                 "action": {"type": "message", "label": "✈️ 規劃追星旅程",
                            "text": "開始規劃"}},
            ],
        },
    })

    # Bubble 2: 近期活動（爬蟲即時）
    import urllib.parse
    search_name = artist.get("search_name", "")
    events = scrape_idol_events(name, country, search_name=search_name, is_actor=is_actor)
    if events:
        event_items = []
        for evt in events[:5]:
            line = f"\U0001f4c5 {evt['date']}"
            if evt.get("venue"):
                line += f"\n   \U0001f3df\ufe0f {evt['venue']}"
            if evt.get("city"):
                line += f"  \U0001f4cd {evt['city']}"
            event_items.append({
                "type": "text", "text": line,
                "size": "sm", "color": "#333333", "wrap": True, "margin": "sm",
            })
        event_body_contents = event_items
        footer_contents = [
            {"type": "button", "style": "link", "height": "sm",
             "action": {"type": "uri", "label": "\U0001f517 \u67e5\u66f4\u591a\u6d3b\u52d5",
                        "uri": f"https://www.bandsintown.com/{urllib.parse.quote(name.lower().replace(' ', '-'))}"}}
        ]
    else:
        enc_search = urllib.parse.quote(search_name if search_name else name)
        event_body_contents = [
            {"type": "text", "text": "目前未查到近期公開活動",
             "size": "sm", "color": "#888888", "wrap": True},
            {"type": "text", "text": "可至以下平台查詢：",
             "size": "xs", "color": "#aaaaaa", "margin": "md"},
        ]
        if is_actor:
            footer_contents = [
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "uri", "label": "🎟 Interpark 粉絲見面會",
                            "uri": f"https://ticket.interpark.com/webzine/paper/TPNoticeList_Calendar.asp?SearchWord={enc_search}"}},
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "uri", "label": "🎟 YES24 Ticket",
                            "uri": f"https://ticket.yes24.com/Category/SearchList?q={enc_search}"}},
            ]
        else:
            slug = urllib.parse.quote((search_name if search_name else name).lower().replace(" ", "-"))
            footer_contents = [
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "uri", "label": "Bandsintown",
                            "uri": f"https://www.bandsintown.com/{slug}"}},
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "uri", "label": "Songkick",
                            "uri": f"https://www.songkick.com/search?query={enc_search}"}},
            ]

    bubbles.append({
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1565C0", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"\U0001f4e2 {name} \u8fd1\u671f\u6d3b\u52d5",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "xs",
            "contents": event_body_contents,
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "paddingAll": "8px",
            "contents": footer_contents,
        },
    })

    # Bubble 3: 周邊商店
    fan_shops = data.get("fan_shops", {}).get(country, [])
    if fan_shops:
        shop_lines = []
        for s in fan_shops[:5]:
            shop_lines.append(f"\U0001f6cd\ufe0f {s['name']}")
            shop_lines.append(f"   {s.get('type', '')} \u2022 {s.get('location', '')}")
            shop_lines.append("")

        bubbles.append({
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#6A1B9A", "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\U0001f6cd\ufe0f \u5468\u908a\u5546\u5e97",
                     "color": "#FFFFFF", "weight": "bold", "size": "md"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "12px",
                "contents": [
                    {"type": "text", "text": "\n".join(shop_lines).strip(),
                     "size": "sm", "color": "#444444", "wrap": True},
                ],
            },
        })

    return [
        {
            "type": "flex",
            "altText": f"\u2b50 {name} \u8ffd\u661f\u8cc7\u8a0a",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]


def _show_scraped_events(artist_name: str, events: list) -> list:
    """顯示爬蟲抓到的活動（Flex Bubble，與 _show_artist_info 同格式）"""
    import urllib.parse
    slug = urllib.parse.quote(artist_name.lower().replace(" ", "-"))

    event_items = []
    for evt in events[:5]:
        line = f"\U0001f4c5 {evt['date']}"
        if evt.get("venue"):
            line += f"\n   \U0001f3df\ufe0f {evt['venue']}"
        if evt.get("city"):
            line += f"  \U0001f4cd {evt['city']}"
        event_items.append({
            "type": "text", "text": line,
            "size": "sm", "color": "#333333", "wrap": True, "margin": "sm",
        })

    bubble = {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": "#1565C0", "paddingAll": "12px",
            "contents": [
                {"type": "text", "text": f"\U0001f4e2 {artist_name} \u8fd1\u671f\u6d3b\u52d5",
                 "color": "#FFFFFF", "weight": "bold", "size": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "12px", "spacing": "xs",
            "contents": event_items,
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "paddingAll": "8px",
            "contents": [
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "uri", "label": "\U0001f517 \u67e5\u66f4\u591a\u6d3b\u52d5",
                            "uri": f"https://www.bandsintown.com/{slug}"}},
                {"type": "button", "style": "link", "height": "sm",
                 "action": {"type": "message", "label": "\u2708\ufe0f \u898f\u5283\u8ffd\u661f\u65c5\u7a0b",
                            "text": "\u958b\u59cb\u898f\u5283"}},
            ],
        },
    }

    return [
        {"type": "flex", "altText": f"\U0001f4e2 {artist_name} \u8fd1\u671f\u6d3b\u52d5",
         "contents": bubble},
    ]
