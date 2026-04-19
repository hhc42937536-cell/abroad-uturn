"""旅程規劃步驟進度條"""

STEP_LABELS = [
    "目的地", "日期", "人數", "機票", "住宿", "行程", "須知", "計畫書"
]

# 進度條格子太窄，只顯示單字
_BAR_LABELS = ["目", "日", "人", "機", "住", "行", "須", "計"]


def build_progress_bar(current_step: int) -> dict:
    """
    建立步驟進度條 Flex Message（步驟 1-8，current_step 為 1-based）
    """
    segments = []
    for i, label in enumerate(_BAR_LABELS):
        step_num = i + 1
        if step_num < current_step:
            # 已完成
            bg = "#FF6B35"
            text_color = "#FFFFFF"
        elif step_num == current_step:
            # 當前步驟
            bg = "#FF6B35"
            text_color = "#FFFFFF"
        else:
            # 未完成
            bg = "#E0E0E0"
            text_color = "#999999"

        segments.append({
            "type": "box", "layout": "vertical",
            "backgroundColor": bg,
            "cornerRadius": "4px",
            "paddingAll": "4px",
            "flex": 1,
            "contents": [
                {
                    "type": "text", "text": label,
                    "size": "xxs", "color": text_color,
                    "align": "center", "weight": "bold",
                },
            ],
        })

    return {
        "type": "box", "layout": "horizontal",
        "spacing": "2px",
        "paddingAll": "8px",
        "contents": segments,
    }


def progress_text(current_step: int) -> str:
    """簡單文字版進度"""
    total = len(STEP_LABELS)
    label = STEP_LABELS[current_step - 1] if 1 <= current_step <= total else ""
    return f"[{current_step}/{total}] {label}"
