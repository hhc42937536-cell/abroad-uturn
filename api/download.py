"""
GET /api/download?token=xxx
從 Redis 讀取已存的行程計畫，回傳 .docx Word 檔供下載
"""

import io
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from bot.services.redis_store import redis_get


# ── 主題色系 ───────────────────────────────────────────
_THEME = {
    "primary":   "1A237E",   # 深藍
    "accent":    "0D47A1",   # 中藍
    "light":     "E3F2FD",   # 淺藍背景
    "header_bg": "1565C0",   # 表格 header 深藍
    "row_alt":   "F5F9FF",   # 表格交替行
    "label_bg":  "E8EAF6",   # 標籤底色
    "section":   "1976D2",   # Section 標題
    "day_bg":    "E1F5FE",   # Day 標題底色
    "insider":   "E8F5E9",   # 在地眉角底色（淡綠）
    "gray":      "757575",
    "divider":   "BBDEFB",
}


def _hex(name: str) -> RGBColor:
    h = _THEME[name]
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _set_cell_bg(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_cell_border(cell, color: str = "BBDEFB"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for side in ("w:top", "w:left", "w:bottom", "w:right"):
        border = OxmlElement(side)
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), "4")
        border.set(qn("w:color"), color)
        tcBorders = tcPr.find(qn("w:tcBorders"))
        if tcBorders is None:
            tcBorders = OxmlElement("w:tcBorders")
            tcPr.append(tcBorders)
        tcBorders.append(border)


def _add_section_heading(doc, text: str, bg_color: str = "1565C0"):
    """色塊背景的 section 標題"""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.rows[0].cells[0]
    _set_cell_bg(cell, bg_color)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(f"  {text}")
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def _add_sub_heading(doc, text: str):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = _hex("section")
    return p


def _add_info_table(doc, rows_data: list[tuple[str, str]]):
    """兩欄資訊表格（label | value）"""
    tbl = doc.add_table(rows=0, cols=2)
    tbl.style = "Table Grid"
    tbl.columns[0].width = Cm(3.5)
    tbl.columns[1].width = Cm(13)
    for i, (label, value) in enumerate(rows_data):
        row = tbl.add_row()
        lbl, val = row.cells[0], row.cells[1]
        bg = _THEME["label_bg"] if i % 2 == 0 else _THEME["row_alt"]
        _set_cell_bg(lbl, _THEME["label_bg"])
        _set_cell_bg(val, bg)
        lp = lbl.paragraphs[0]
        lr = lp.add_run(label)
        lr.bold = True
        lr.font.size = Pt(9)
        lr.font.color.rgb = _hex("accent")
        vp = val.paragraphs[0]
        vr = vp.add_run(value)
        vr.font.size = Pt(9)
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)


def _add_day_block(doc, day: dict):
    """每日行程 — 帶底色的日期標題 + 三格時段"""
    title = day.get("title", "")
    date_label = day.get("date_label", "")
    header = f"{title}  {date_label}".strip()

    # 日期標題列
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.rows[0].cells[0]
    _set_cell_bg(cell, _THEME["day_bg"])
    p = cell.paragraphs[0]
    run = p.add_run(f"  {header}")
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = _hex("accent")

    # 三時段
    slots = [
        ("🌅 上午", day.get("am", "")),
        ("☀️ 下午", day.get("pm", "")),
        ("🌙 晚上", day.get("eve", "")),
    ]
    for icon, val in slots:
        if not val:
            continue
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        icon_run = p.add_run(f"{icon}  ")
        icon_run.bold = True
        icon_run.font.size = Pt(9)
        icon_run.font.color.rgb = _hex("gray")
        val_run = p.add_run(val)
        val_run.font.size = Pt(9)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def _build_docx(plan: dict) -> bytes:
    doc = Document()

    # ── 頁面設定 ───────────────────────────────────────
    sec = doc.sections[0]
    sec.page_width    = Cm(21)
    sec.page_height   = Cm(29.7)
    sec.left_margin   = Cm(2.2)
    sec.right_margin  = Cm(2.2)
    sec.top_margin    = Cm(2.0)
    sec.bottom_margin = Cm(2.0)

    flag      = plan.get("flag", "✈️")
    city      = plan.get("city", "")
    days_text = plan.get("days_text", "")

    # ── 主標題（深藍色塊）────────────────────────────────
    tbl_title = doc.add_table(rows=2, cols=1)
    tbl_title.style = "Table Grid"
    # Row 1：城市名
    c1 = tbl_title.rows[0].cells[0]
    _set_cell_bg(c1, _THEME["primary"])
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p1.add_run(f"{flag}  {city}  行程計畫書")
    r1.bold = True
    r1.font.size = Pt(22)
    r1.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p1.paragraph_format.space_before = Pt(8)
    p1.paragraph_format.space_after = Pt(4)
    # Row 2：日期副標
    c2 = tbl_title.rows[1].cells[0]
    _set_cell_bg(c2, _THEME["accent"])
    p2 = c2.paragraphs[0]
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(days_text)
    r2.font.size = Pt(11)
    r2.font.color.rgb = RGBColor(0xE3, 0xF2, 0xFD)
    p2.paragraph_format.space_before = Pt(4)
    p2.paragraph_format.space_after = Pt(6)

    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)

    # ── 基本資料 ─────────────────────────────────────────
    _add_section_heading(doc, "📋  基本資料")
    rows_base = [
        ("目的地", f"{flag}  {city}"),
        ("出發地", f"{plan.get('origin_name', '')}  →  {city}"),
        ("日期",   plan.get("date_display", "")),
        ("人數",   f"{plan.get('adults', 1)} 人"),
    ]
    if plan.get("budget"):
        rows_base.append(("預算", f"NT${plan['budget']:,}"))
    _add_info_table(doc, rows_base)

    # ── 旅遊資訊 ─────────────────────────────────────────
    info_rows = []
    if plan.get("flight_text"):
        info_rows.append(("✈️ 機票",   plan["flight_text"]))
    if plan.get("hotel_pref"):
        info_rows.append(("🏨 住宿",   plan["hotel_pref"]))
    if plan.get("visa_text"):
        info_rows.append(("📘 簽證",   plan["visa_text"]))
    if plan.get("weather_text"):
        info_rows.append(("🌤 天氣",   plan["weather_text"]))
    if plan.get("exchange_text"):
        info_rows.append(("💱 匯率",   plan["exchange_text"]))
    if plan.get("plug_text"):
        info_rows.append(("🔌 插座",   plan["plug_text"]))
    if plan.get("custom"):
        info_rows.append(("📝 特別需求", plan["custom"]))

    if info_rows:
        _add_section_heading(doc, "🗺  旅遊資訊")
        _add_info_table(doc, info_rows)

    # ── 天天行程 ─────────────────────────────────────────
    itinerary = plan.get("itinerary", [])
    if itinerary:
        _add_section_heading(doc, "📅  天天行程")
        for day in itinerary:
            _add_day_block(doc, day)

    # ── 在地眉角 ─────────────────────────────────────────
    insider = plan.get("insider", {})
    if insider:
        _add_section_heading(doc, f"✨  {city} 在地眉角", bg_color="1B5E20")
        sections = [
            ("🎟️ 票務時機",  insider.get("ticket", [])),
            ("👥 人潮規律",  insider.get("crowd", [])),
            ("🚇 交通秘技",  insider.get("transport", [])),
            ("🗺️ 隱藏景點",  insider.get("hidden", [])),
            ("💰 省錢技巧",  insider.get("money", [])),
        ]
        for sec_title, items in sections:
            if not items:
                continue
            _add_sub_heading(doc, sec_title)
            for item in items:
                p = doc.add_paragraph(style="List Bullet")
                p.paragraph_format.left_indent = Cm(0.5)
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                run = p.add_run(item)
                run.font.size = Pt(9)
        sp2 = doc.add_paragraph()
        sp2.paragraph_format.space_after = Pt(4)

    # ── 必吃清單 ─────────────────────────────────────────
    must_eat = plan.get("must_eat", [])
    if must_eat:
        _add_section_heading(doc, f"🍜  {city} 必吃清單", bg_color="B71C1C")
        for item in must_eat:
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.space_before = Pt(1)
            run = p.add_run(item)
            run.font.size = Pt(10)
        doc.add_paragraph()

    # ── 頁尾 ─────────────────────────────────────────────
    tbl_footer = doc.add_table(rows=1, cols=1)
    tbl_footer.style = "Table Grid"
    cf = tbl_footer.rows[0].cells[0]
    _set_cell_bg(cf, _THEME["light"])
    pf = cf.paragraphs[0]
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rf = pf.add_run("⚠️ 簽證/海關資訊僅供參考，以官方公告為準    |    由「出國優轉」LINE Bot 生成")
    rf.font.size = Pt(8)
    rf.font.color.rgb = _hex("gray")
    pf.paragraph_format.space_before = Pt(4)
    pf.paragraph_format.space_after = Pt(4)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self._handle_get()
        except Exception as e:
            print(f"[download] unhandled: {traceback.format_exc()}")
            try:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
            except Exception:
                pass

    def _handle_get(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        token  = params.get("token", [None])[0]

        if not token:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing token")
            return

        raw = redis_get(f"download:{token}")
        if not raw:
            self.send_response(404)
            self.end_headers()
            self.wfile.write("找不到行程，連結已過期（72小時）".encode("utf-8"))
            return

        try:
            plan = json.loads(raw)
        except Exception:
            self.send_response(500)
            self.end_headers()
            return

        try:
            content = _build_docx(plan)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))
            return

        city         = plan.get("city", "行程")
        date_display = plan.get("date_display", "").replace("/", "-").replace(" ~ ", "_")
        filename     = f"{city}_{date_display}_計畫書.docx"
        from urllib.parse import quote
        encoded_name = quote(filename, safe="")

        self.send_response(200)
        self.send_header("Content-Type",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.send_header("Content-Disposition",
            f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_name}')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass
