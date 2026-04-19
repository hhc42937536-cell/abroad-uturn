"""各步驟的 Flex Message 模板"""

def step_bubble(step: int, title: str, body_contents: list,
                footer_contents: list = None, header_color: str = "#FF6B35") -> dict:
    """通用步驟卡片模板"""
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": header_color,
            "paddingAll": "15px",
            "contents": [
                {
                    "type": "text", "text": title,
                    "color": "#FFFFFF", "weight": "bold", "size": "lg",
                },
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "spacing": "md", "paddingAll": "15px",
            "contents": body_contents,
        },
    }
    if footer_contents:
        bubble["footer"] = {
            "type": "box", "layout": "vertical",
            "spacing": "sm", "paddingAll": "10px",
            "contents": footer_contents,
        }
    return bubble


def postback_button(label: str, data: str, style: str = "primary",
                    color: str = "#FF6B35") -> dict:
    """建立 Postback 按鈕"""
    return {
        "type": "button", "style": style, "color": color, "height": "sm",
        "action": {"type": "postback", "label": label, "data": data},
    }


def message_button(label: str, text: str, style: str = "secondary",
                   color: str = "#AAAAAA") -> dict:
    """建立 Message 按鈕"""
    return {
        "type": "button", "style": style, "color": color, "height": "sm",
        "action": {"type": "message", "label": label, "text": text},
    }


def quick_reply_item(label: str, text: str) -> dict:
    """建立 Quick Reply 項目"""
    return {
        "type": "action",
        "action": {"type": "message", "label": label, "text": text},
    }


def quick_reply_postback(label: str, data: str, display_text: str = "") -> dict:
    """建立 Postback Quick Reply 項目"""
    action = {"type": "postback", "label": label, "data": data}
    if display_text:
        action["displayText"] = display_text
    return {"type": "action", "action": action}
