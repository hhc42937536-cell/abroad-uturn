#!/usr/bin/env python3
"""
LINE Rich Menu 建立腳本（3x3 九格版）— 出國優轉 AbroadUturn
==========================================================
產生 Rich Menu 圖片並透過 LINE API 建立、上傳、設為預設。

使用方式：
  pip install Pillow
  python create_rich_menu.py --token 你的Channel_Access_Token

  # 或只生圖不部署：
  python create_rich_menu.py --image-only

  # 使用自訂 9 張小圖合成（放在 rich_menu_tiles/ 資料夾）：
  python create_rich_menu.py --token TOKEN --tiles-dir rich_menu_tiles
"""

import os, sys, json, io, argparse
import urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── 指令列參數 ────────────────────────────────────────
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--token",      default="", help="LINE Channel Access Token")
_parser.add_argument("--image-only", action="store_true", help="只生圖，不部署到 LINE")
_parser.add_argument("--tiles-dir",  default="rich_menu_tiles", help="9 張小圖資料夾")
_args, _ = _parser.parse_known_args()

# ── 設定 ─────────────────────────────────────────────
LINE_TOKEN = _args.token or os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
OUTPUT_IMAGE = "rich_menu.jpg"

# 圖片尺寸（LINE 標準，3x3 九格版）
IMG_W, IMG_H = 2500, 1686
COLS, ROWS = 3, 3
COL_WS = [833, 834, 833]
ROW_HS = [562, 562, 562]

# 9 格內容（左上 → 右 → 下一排）
CELLS = [
    # 上排：核心功能
    {"label": "便宜國外探索",  "sub": "近期最便宜目的地",    "icon": "\u2708\ufe0f\U0001f30d", "text": "便宜"},
    {"label": "機票比價",      "sub": "多平台即時比價",      "icon": "\U0001f4ca\U0001f4b0", "text": "機票比價"},
    {"label": "彈性日期",      "sub": "找最便宜的出發日",    "icon": "\U0001f4c5\U0001f504", "text": "彈性日期"},
    # 中排
    {"label": "直飛優先",      "sub": "舒適直飛含稅總價",    "icon": "\U0001f6eb\U0001f680", "text": "直飛"},
    {"label": "轉機最省",      "sub": "最低總價轉機方案",    "icon": "\U0001f504\U0001f4b8", "text": "轉機"},
    {"label": "機+酒打包",     "sub": "最低組合總價",        "icon": "\U0001f3e8\u2708\ufe0f", "text": "機加酒"},
    # 下排
    {"label": "熱門國家",      "sub": "日韓泰東南亞歐洲",    "icon": "\U0001f1ef\U0001f1f5\U0001f1f0\U0001f1f7", "text": "熱門國家"},
    {"label": "旅行工具箱",    "sub": "出發地/打包/簽證/天氣",  "icon": "\U0001f9f3\U0001f6e1\ufe0f", "text": "旅行工具"},
    {"label": "價格追蹤",      "sub": "降價立即通知你",      "icon": "\U0001f514\U0001f4c9", "text": "我的追蹤"},
]

# 色系（旅遊暖橘主題）
BG_COLOR    = "#1A1A2E"   # 全圖背景（深藍紫）
CELL_SEL    = "#16213E"   # 上排格子（深藍）
CELL_MID    = "#0F3460"   # 中排格子（藍）
CELL_COLOR  = "#1A1A2E"   # 下排格子（最深）
SEP_COLOR   = "#FFFFFF22" # 分隔線
ICON_COLOR  = "#FFFFFF"
LABEL_COLOR = "#FFFFFF"
SUB_COLOR   = "#7FAACC"

FONT_ZH   = "C:/Windows/Fonts/msjhbd.ttc"   # Microsoft JhengHei Bold
FONT_EMOJI = "C:/Windows/Fonts/seguiemj.ttf" # Segoe UI Emoji


# ── LINE API 工具 ─────────────────────────────────────
def line_api(method: str, path: str, body=None, content_type="application/json"):
    url = f"https://api.line.me{path}"
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        else:
            data = body
            headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LINE API {e.code}: {e.read().decode('utf-8', 'ignore')}")


def line_data_api(method: str, path: str, data: bytes, content_type: str):
    url = f"https://api-data.line.me{path}"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": content_type,
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"LINE Data API {e.code}: {e.read().decode('utf-8', 'ignore')}")


# ── 圖片產生 ─────────────────────────────────────────
def generate_image() -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (IMG_W, IMG_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    col_xs = [sum(COL_WS[:c]) for c in range(COLS)]
    row_ys = [sum(ROW_HS[:r]) for r in range(ROWS)]

    try:
        font_icon  = ImageFont.truetype(FONT_EMOJI, 130)
        font_label = ImageFont.truetype(FONT_ZH, 68)
        font_sub   = ImageFont.truetype(FONT_ZH, 38)
    except Exception as e:
        print(f"  警告：字型載入失敗 ({e})，使用預設字型")
        font_icon = font_label = font_sub = ImageFont.load_default()

    for i, cell in enumerate(CELLS):
        row = i // COLS
        col = i % COLS
        x = col_xs[col]
        y = row_ys[row]
        cw = COL_WS[col]
        ch = ROW_HS[row]
        cx = x + cw // 2
        cy = y + ch // 2

        bg = CELL_SEL if row == 0 else (CELL_MID if row == 1 else CELL_COLOR)
        pad = 6
        draw.rounded_rectangle(
            [x + pad, y + pad, x + cw - pad, y + ch - pad],
            radius=20, fill=bg
        )

        if col > 0:
            draw.line([(x, y), (x, y + ch)], fill=SEP_COLOR, width=2)
        if row > 0:
            draw.line([(x, y), (x + cw, y)], fill=SEP_COLOR, width=2)

        # Icon
        icon_y = cy - 100
        icon_text = cell["icon"][:2]  # 最多取 2 個 emoji
        try:
            draw.text((cx, icon_y), icon_text, fill=ICON_COLOR,
                      font=font_icon, anchor="mm", embedded_color=True)
        except TypeError:
            draw.text((cx, icon_y), icon_text, fill=ICON_COLOR,
                      font=font_icon, anchor="mm")

        # 主標題
        draw.text((cx, cy + 15), cell["label"], fill=LABEL_COLOR,
                  font=font_label, anchor="mm")

        # 副標題
        draw.text((cx, cy + 70), cell["sub"], fill=SUB_COLOR,
                  font=font_sub, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True)
    data = buf.getvalue()
    print(f"  圖片大小: {len(data):,} bytes ({len(data)/1024:.0f} KB)")
    return data


# ── 合成小圖版 ───────────────────────────────────────
def generate_from_tiles(tiles_dir: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (IMG_W, IMG_H), "#F5F5F5")
    draw = ImageDraw.Draw(img)
    col_xs = [sum(COL_WS[:c]) for c in range(COLS)]
    row_ys = [sum(ROW_HS[:r]) for r in range(ROWS)]

    try:
        font_label = ImageFont.truetype(FONT_ZH, 100)
        font_sub   = ImageFont.truetype(FONT_ZH, 54)
    except Exception:
        font_label = font_sub = ImageFont.load_default()

    TOP_COLORS = [
        "#FF6B35", "#2196F3", "#4CAF50",
        "#FF9800", "#9C27B0", "#E91E63",
        "#00BCD4", "#795548", "#607D8B",
    ]

    TEXT_AREA_H = 190

    found = 0
    for i, cell in enumerate(CELLS):
        row = i // COLS; col = i % COLS
        x = col_xs[col]; y = row_ys[row]
        cw = COL_WS[col]; ch = ROW_HS[row]
        cx = x + cw // 2

        draw.rectangle([x, y, x+cw, y+ch], fill="#FFFFFF")
        draw.line([(x+cw, y), (x+cw, y+ch)], fill="#E0E0E0", width=3)
        draw.line([(x, y+ch), (x+cw, y+ch)], fill="#E0E0E0", width=3)
        draw.rectangle([x, y, x+cw, y+10], fill=TOP_COLORS[i])

        # 嘗試載入小圖
        tile_path = None
        for ext in ("jpg", "jpeg", "png", "webp"):
            p = os.path.join(tiles_dir, f"{i}.{ext}")
            if os.path.isfile(p):
                tile_path = p; break

        if tile_path:
            try:
                tile = Image.open(tile_path).convert("RGB")
                pic_h = ch - TEXT_AREA_H - 10
                ratio = min(cw / tile.width, pic_h / tile.height)
                new_w = int(tile.width * ratio)
                new_h = int(tile.height * ratio)
                tile = tile.resize((new_w, new_h), Image.LANCZOS)
                px = x + (cw - new_w) // 2
                py = y + 14
                img.paste(tile, (px, py))
                found += 1
            except Exception as e:
                print(f"  小圖 {tile_path} 載入失敗: {e}")

        # 文字區
        text_y = y + ch - TEXT_AREA_H
        draw.rectangle([x+4, text_y, x+cw-4, y+ch-4], fill="#FFFFFF")
        draw.text((cx, text_y + 50), cell["label"], fill="#333333",
                  font=font_label, anchor="mm")
        draw.text((cx, text_y + 130), cell["sub"], fill="#888888",
                  font=font_sub, anchor="mm")

    print(f"  找到 {found}/9 張小圖")

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90, optimize=True)
    data = buf.getvalue()
    print(f"  圖片大小: {len(data):,} bytes ({len(data)/1024:.0f} KB)")
    return data


# ── Rich Menu API ────────────────────────────────────
def build_areas():
    col_xs = [sum(COL_WS[:c]) for c in range(COLS)]
    row_ys = [sum(ROW_HS[:r]) for r in range(ROWS)]
    areas = []
    for i, cell in enumerate(CELLS):
        row = i // COLS
        col = i % COLS
        areas.append({
            "bounds": {
                "x": col_xs[col], "y": row_ys[row],
                "width": COL_WS[col], "height": ROW_HS[row],
            },
            "action": {
                "type": "message",
                "label": cell["label"][:20],
                "text": cell["text"],
            }
        })
    return areas


def create_rich_menu() -> str:
    body = {
        "size": {"width": IMG_W, "height": IMG_H},
        "selected": True,
        "name": "出國優轉選單 v1（3x3）",
        "chatBarText": "\u2728 \u9ede\u6211\u958b\u59cb\u63a2\u7d22\u4fbf\u5b9c\u6a5f\u7968",
        "areas": build_areas(),
    }
    result = line_api("POST", "/v2/bot/richmenu", body)
    return result["richMenuId"]


def upload_image(menu_id: str, img_data: bytes):
    line_data_api(
        "POST", f"/v2/bot/richmenu/{menu_id}/content",
        img_data, "image/jpeg"
    )


def set_default(menu_id: str):
    line_api("POST", f"/v2/bot/user/all/richmenu/{menu_id}")


def delete_old_menus(keep_id: str):
    result = line_api("GET", "/v2/bot/richmenu/list")
    for m in result.get("richmenus", []):
        mid = m["richMenuId"]
        if mid != keep_id:
            try:
                line_api("DELETE", f"/v2/bot/richmenu/{mid}")
                print(f"  刪除舊選單: {mid}")
            except Exception as e:
                print(f"  刪除失敗 {mid}: {e}")


# ── 主程式 ───────────────────────────────────────────
def main():
    print("\n\u2708\ufe0f 出國優轉 Rich Menu 建立工具")
    print("=" * 40)

    # 生成圖片
    tiles_dir = _args.tiles_dir
    if os.path.isdir(tiles_dir) and any(
        os.path.isfile(os.path.join(tiles_dir, f"{i}.{ext}"))
        for i in range(9) for ext in ("jpg", "png", "webp")
    ):
        print(f"\n\U0001f3a8 使用小圖合成模式（{tiles_dir}/）")
        img_data = generate_from_tiles(tiles_dir)
    else:
        print("\n\U0001f3a8 使用 emoji 生成模式")
        img_data = generate_image()

    # 存檔
    with open(OUTPUT_IMAGE, "wb") as f:
        f.write(img_data)
    print(f"  \u2705 已存檔: {OUTPUT_IMAGE}")

    if _args.image_only:
        print("\n  --image-only 模式，不部署到 LINE")
        return

    if not LINE_TOKEN:
        print("\n  \u26a0\ufe0f 未提供 --token，跳過 LINE API 部署")
        print("  請用 --token YOUR_TOKEN 或設定環境變數 LINE_CHANNEL_ACCESS_TOKEN")
        return

    # 建立 Rich Menu
    print("\n\U0001f4e4 建立 Rich Menu...")
    menu_id = create_rich_menu()
    print(f"  Rich Menu ID: {menu_id}")

    # 上傳圖片
    print("\U0001f4f7 上傳圖片...")
    upload_image(menu_id, img_data)
    print("  \u2705 上傳成功")

    # 設為預設
    print("\U0001f3af 設為預設選單...")
    set_default(menu_id)
    print("  \u2705 設定成功")

    # 刪除舊的
    print("\U0001f5d1\ufe0f 清理舊選單...")
    delete_old_menus(menu_id)

    print(f"\n\u2728 完成！Rich Menu 已部署")
    print(f"  Menu ID: {menu_id}")


if __name__ == "__main__":
    main()
