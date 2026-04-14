"""月份選擇器 Flex Carousel"""


def month_picker_flex() -> list:
    """建立月份選擇器 Flex Carousel"""
    import datetime
    today = datetime.date.today()

    month_names = ["1月", "2月", "3月", "4月", "5月", "6月",
                   "7月", "8月", "9月", "10月", "11月", "12月"]
    month_themes = [
        ("#4FC3F7", "\u2744\ufe0f", "冬季特惠"),
        ("#F48FB1", "\U0001f338", "早春賞花"),
        ("#CE93D8", "\U0001f338", "櫻花季節"),
        ("#81C784", "\U0001f30f", "說走就走"),
        ("#FFD54F", "\u2600\ufe0f", "初夏出遊"),
        ("#FF8A65", "\u2600\ufe0f", "暑假開跑"),
        ("#4DD0E1", "\U0001f3d6\ufe0f", "海島度假"),
        ("#4DB6AC", "\U0001f3d6\ufe0f", "盛夏旅行"),
        ("#FFB74D", "\U0001f341", "秋季旅遊"),
        ("#FF8A65", "\U0001f341", "賞楓季節"),
        ("#A1887F", "\U0001f342", "深秋優惠"),
        ("#90A4AE", "\u2744\ufe0f", "跨年搶票"),
    ]

    bubbles = []
    for i in range(6):
        y = today.year + (today.month + i - 1) // 12
        m = (today.month + i - 1) % 12 + 1
        month_str = f"{y}-{m:02d}"
        bg_color, emoji, desc = month_themes[m - 1]
        name = month_names[m - 1]

        bubbles.append({
            "type": "bubble",
            "size": "micro",
            "styles": {"body": {"backgroundColor": bg_color}},
            "body": {
                "type": "box", "layout": "vertical",
                "justifyContent": "center", "alignItems": "center",
                "paddingAll": "18px", "spacing": "sm",
                "contents": [
                    {"type": "text", "text": emoji, "size": "4xl", "align": "center"},
                    {"type": "text", "text": f"{y}",
                     "size": "xxs", "color": "#FFFFFFBB", "align": "center", "margin": "md"},
                    {"type": "text", "text": name,
                     "size": "xl", "weight": "bold", "color": "#FFFFFF", "align": "center"},
                    {"type": "text", "text": desc,
                     "size": "xs", "color": "#FFFFFFDD", "align": "center"},
                    {"type": "box", "layout": "vertical",
                     "backgroundColor": "#FFFFFF33", "cornerRadius": "md",
                     "paddingAll": "8px", "margin": "md",
                     "contents": [
                         {"type": "text", "text": "\u2708\ufe0f \u9ede\u6211\u63a2\u7d22",
                          "size": "sm", "color": "#FFFFFF", "align": "center", "weight": "bold"},
                     ]},
                ],
                "action": {
                    "type": "message", "label": name,
                    "text": f"\u63a2\u7d22|{month_str}",
                },
            },
        })

    return [
        {"type": "text", "text": "\U0001f30d \u9078\u64c7\u51fa\u767c\u6708\u4efd\uff0c\u5e6b\u4f60\u627e\u6700\u4fbf\u5b9c\u7684\u76ee\u7684\u5730\uff01"},
        {
            "type": "flex",
            "altText": "\u9078\u64c7\u51fa\u767c\u6708\u4efd",
            "contents": {"type": "carousel", "contents": bubbles},
        },
    ]
