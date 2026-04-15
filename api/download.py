"""
GET /api/download?token=xxx
從 Redis 讀取已存的行程計畫，回傳 .txt 純文字檔供下載
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from bot.services.redis_store import redis_get


def _build_text(plan: dict) -> str:
    lines = []
    lines.append("=" * 40)
    lines.append("  出國計畫書")
    lines.append("=" * 40)
    lines.append("")

    flag = plan.get("flag", "✈️")
    city = plan.get("city", "")
    days_text = plan.get("days_text", "")
    lines.append(f"目的地：{flag} {city}  {days_text}")
    lines.append(f"出發地：{plan.get('origin_name', '')} → {city}")
    lines.append(f"日期：{plan.get('date_display', '')}")
    lines.append(f"人數：{plan.get('adults', 1)} 人")
    budget = plan.get("budget", 0)
    if budget:
        lines.append(f"預算：NT${budget:,}")
    lines.append("")
    lines.append("-" * 40)

    flight_text = plan.get("flight_text", "")
    if flight_text:
        lines.append(f"✈️  機票：{flight_text}")
    hotel = plan.get("hotel_pref", "")
    if hotel:
        lines.append(f"🏨 住宿：{hotel}")
    visa = plan.get("visa_text", "")
    if visa:
        lines.append(f"📘 簽證：{visa}")
    weather = plan.get("weather_text", "")
    if weather:
        lines.append(f"☀️  天氣：{weather}")
    exchange = plan.get("exchange_text", "")
    if exchange:
        lines.append(f"💱 匯率：{exchange}")
    plug = plan.get("plug_text", "")
    if plug:
        lines.append(f"🔌 插座：{plug}")
    custom = plan.get("custom", "")
    if custom:
        lines.append(f"📝 備註：{custom}")

    # 天天行程
    itinerary = plan.get("itinerary", [])
    if itinerary:
        lines.append("")
        lines.append("=" * 40)
        lines.append("  天天行程")
        lines.append("=" * 40)
        for day in itinerary:
            lines.append("")
            lines.append(f"【{day.get('title', '')}】{day.get('date_label', '')}")
            if day.get("am"):
                lines.append(f"  🌅 上午  {day['am']}")
            if day.get("pm"):
                lines.append(f"  ☀️  下午  {day['pm']}")
            if day.get("eve"):
                lines.append(f"  🌙 晚上  {day['eve']}")

    # 必吃
    must_eat = plan.get("must_eat", [])
    if must_eat:
        lines.append("")
        lines.append("=" * 40)
        lines.append(f"  {city} 必吃清單")
        lines.append("=" * 40)
        for item in must_eat:
            lines.append(f"  • {item}")

    lines.append("")
    lines.append("=" * 40)
    lines.append("⚠️  簽證/海關資訊僅供參考，請以官方公告為準")
    lines.append("   由「出國優轉」LINE Bot 生成")
    lines.append("=" * 40)
    return "\n".join(lines)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        token = params.get("token", [None])[0]

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

        city = plan.get("city", "行程")
        date_display = plan.get("date_display", "").replace("/", "-").replace(" ~ ", "_")
        filename = f"{city}_{date_display}_計畫書.txt"

        content = _build_text(plan).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition",
                         f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args):
        pass
