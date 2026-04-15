"""
GET /api/download?token=xxx
從 Redis 讀取已存的行程計畫，回傳 .docx Word 檔供下載
"""

import io
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from bot.services.redis_store import redis_get


def _set_cell_bg(cell, hex_color: str):
    """設定表格儲存格背景色"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _add_heading(doc, text: str, level: int = 1):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.runs[0] if p.runs else p.add_run(text)
    if level == 1:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)   # dark blue
        run.font.size = Pt(16)
    elif level == 2:
        run.font.color.rgb = RGBColor(0x0D, 0x47, 0xA1)
        run.font.size = Pt(13)
    else:
        run.font.color.rgb = RGBColor(0x37, 0x47, 0x4F)
        run.font.size = Pt(11)
    return p


def _add_info_row(table, label: str, value: str):
    row = table.add_row()
    lbl_cell = row.cells[0]
    val_cell = row.cells[1]
    _set_cell_bg(lbl_cell, "E8EAF6")
    lbl_run = lbl_cell.paragraphs[0].add_run(label)
    lbl_run.bold = True
    lbl_run.font.size = Pt(10)
    val_run = val_cell.paragraphs[0].add_run(value)
    val_run.font.size = Pt(10)


def _build_docx(plan: dict) -> bytes:
    doc = Document()

    # ── 頁面設定 ───────────────────────────────────────
    section = doc.sections[0]
    section.page_width  = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)

    flag      = plan.get("flag", "✈️")
    city      = plan.get("city", "")
    days_text = plan.get("days_text", "")

    # ── 標題 ───────────────────────────────────────────
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(f"{flag} {city} 行程計畫書")
    title_run.bold = True
    title_run.font.size = Pt(20)
    title_run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run(days_text)
    sub_run.font.size = Pt(12)
    sub_run.font.color.rgb = RGBColor(0x78, 0x90, 0x9C)

    doc.add_paragraph()

    # ── 基本資料表格 ────────────────────────────────────
    _add_heading(doc, "基本資料", level=1)
    tbl = doc.add_table(rows=0, cols=2)
    tbl.style = "Table Grid"
    tbl.columns[0].width = Cm(4)
    tbl.columns[1].width = Cm(12)

    rows_data = [
        ("目的地", f"{flag} {city}"),
        ("出發地", f"{plan.get('origin_name', '')} → {city}"),
        ("日期",   plan.get("date_display", "")),
        ("人數",   f"{plan.get('adults', 1)} 人"),
    ]
    budget = plan.get("budget", 0)
    if budget:
        rows_data.append(("預算", f"NT${budget:,}"))

    for label, value in rows_data:
        _add_info_row(tbl, label, value)

    doc.add_paragraph()

    # ── 旅遊資訊表格 ────────────────────────────────────
    info_rows = []
    if plan.get("flight_text"):
        info_rows.append(("✈️  機票",  plan["flight_text"]))
    if plan.get("hotel_pref"):
        info_rows.append(("🏨 住宿",  plan["hotel_pref"]))
    if plan.get("visa_text"):
        info_rows.append(("📘 簽證",  plan["visa_text"]))
    if plan.get("weather_text"):
        info_rows.append(("☀️  天氣",  plan["weather_text"]))
    if plan.get("exchange_text"):
        info_rows.append(("💱 匯率",  plan["exchange_text"]))
    if plan.get("plug_text"):
        info_rows.append(("🔌 插座",  plan["plug_text"]))
    if plan.get("custom"):
        info_rows.append(("📝 備註",  plan["custom"]))

    if info_rows:
        _add_heading(doc, "旅遊資訊", level=1)
        tbl2 = doc.add_table(rows=0, cols=2)
        tbl2.style = "Table Grid"
        tbl2.columns[0].width = Cm(4)
        tbl2.columns[1].width = Cm(12)
        for label, value in info_rows:
            _add_info_row(tbl2, label, value)
        doc.add_paragraph()

    # ── 天天行程 ────────────────────────────────────────
    itinerary = plan.get("itinerary", [])
    if itinerary:
        _add_heading(doc, "天天行程", level=1)
        for day in itinerary:
            title_text = day.get("title", "")
            date_label = day.get("date_label", "")
            heading = f"{title_text}  {date_label}".strip()
            _add_heading(doc, heading, level=2)

            for slot_icon, slot_key in [("🌅 上午", "am"), ("☀️  下午", "pm"), ("🌙 晚上", "eve")]:
                val = day.get(slot_key, "")
                if val:
                    p = doc.add_paragraph(style="List Bullet")
                    run = p.add_run(f"{slot_icon}  {val}")
                    run.font.size = Pt(10)

        doc.add_paragraph()

    # ── 必吃清單 ────────────────────────────────────────
    must_eat = plan.get("must_eat", [])
    if must_eat:
        _add_heading(doc, f"{city} 必吃清單", level=1)
        for item in must_eat:
            p = doc.add_paragraph(style="List Bullet")
            run = p.add_run(item)
            run.font.size = Pt(10)
        doc.add_paragraph()

    # ── 免責聲明 ────────────────────────────────────────
    disclaimer_p = doc.add_paragraph()
    disclaimer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    d_run = disclaimer_p.add_run("⚠️  簽證/海關資訊僅供參考，請以官方公告為準")
    d_run.font.size = Pt(9)
    d_run.font.color.rgb = RGBColor(0x78, 0x78, 0x78)

    credit_p = doc.add_paragraph()
    credit_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_run = credit_p.add_run("由「出國優轉」LINE Bot 生成")
    c_run.font.size = Pt(9)
    c_run.font.color.rgb = RGBColor(0x78, 0x78, 0x78)

    # ── 輸出為 bytes ────────────────────────────────────
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
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
        # RFC 5987 encoding for non-ASCII filename
        from urllib.parse import quote
        encoded_name = quote(filename, safe="")

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_name}'
        )
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass
