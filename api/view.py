"""
GET /api/view?token=xxx
從 Redis 讀取已存的行程計畫，回傳美化 HTML（可由瀏覽器列印成 PDF）
"""

import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jinja2 import Environment, FileSystemLoader, select_autoescape
from bot.services.redis_store import redis_get

# 城市主題色（primary, accent, light）
_CITY_THEME: dict[str, dict] = {
    "TYO": {"primary": "#1a237e", "accent": "#1565c0", "light": "#e3f2fd"},
    "OSA": {"primary": "#880e4f", "accent": "#ad1457", "light": "#fce4ec"},
    "KIX": {"primary": "#880e4f", "accent": "#ad1457", "light": "#fce4ec"},
    "CTS": {"primary": "#1a237e", "accent": "#0277bd", "light": "#e1f5fe"},
    "OKA": {"primary": "#006064", "accent": "#00838f", "light": "#e0f7fa"},
    "FUK": {"primary": "#1a237e", "accent": "#283593", "light": "#e8eaf6"},
    "SEL": {"primary": "#37474f", "accent": "#546e7a", "light": "#eceff1"},
    "BKK": {"primary": "#b71c1c", "accent": "#c62828", "light": "#ffebee"},
    "CNX": {"primary": "#1b5e20", "accent": "#2e7d32", "light": "#e8f5e9"},
    "SIN": {"primary": "#e65100", "accent": "#f57c00", "light": "#fff3e0"},
    "KUL": {"primary": "#1a237e", "accent": "#283593", "light": "#e8eaf6"},
    "DPS": {"primary": "#004d40", "accent": "#00695c", "light": "#e0f2f1"},
    "SGN": {"primary": "#1b5e20", "accent": "#388e3c", "light": "#e8f5e9"},
    "HAN": {"primary": "#b71c1c", "accent": "#d32f2f", "light": "#ffebee"},
    "DAD": {"primary": "#006064", "accent": "#0097a7", "light": "#e0f7fa"},
    "MFM": {"primary": "#37474f", "accent": "#455a64", "light": "#eceff1"},
    "MNL": {"primary": "#1565c0", "accent": "#1976d2", "light": "#e3f2fd"},
    "PAR": {"primary": "#4a148c", "accent": "#6a1b9a", "light": "#f3e5f5"},
    "ROM": {"primary": "#b71c1c", "accent": "#c62828", "light": "#ffebee"},
    "TPE": {"primary": "#1a237e", "accent": "#1565c0", "light": "#e3f2fd"},
}
_DEFAULT_THEME = {"primary": "#1a237e", "accent": "#1565c0", "light": "#e3f2fd"}

_TMPL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "bot", "templates",
)
_jinja_env = Environment(
    loader=FileSystemLoader(_TMPL_DIR),
    autoescape=select_autoescape(["html"]),
)


def render_plan_html(plan: dict) -> str:
    """將 plan dict 渲染成美化 HTML 字串。"""
    tmpl = _jinja_env.get_template("travel_plan.html")
    dest_code = plan.get("dest_code", "")
    theme = _CITY_THEME.get(dest_code, _DEFAULT_THEME)
    now = datetime.now().strftime("%Y/%m/%d")
    return tmpl.render(**plan, theme=theme, generated_at=now)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        token  = params.get("token", [None])[0]

        if not token:
            self._err(400, "Missing token")
            return

        raw = redis_get(f"download:{token}")
        if not raw:
            self._err(404, "找不到行程，連結已過期（72 小時）")
            return

        try:
            plan = json.loads(raw)
        except Exception:
            self._err(500, "資料格式錯誤")
            return

        # ── 懶生成：hotel_recs 和 tagline 在此處補齊 ──
        updated = False
        if not plan.get("hotel_recs"):
            try:
                from bot.utils.itinerary_builder import get_hotel_recs
                dest_code = plan.get("dest_code", "")
                city = plan.get("city", "")
                budget_num = plan.get("budget", 0)
                budget_str = f"NT${budget_num:,}" if budget_num else ""
                adults = plan.get("adults", 1)
                recs = get_hotel_recs(dest_code, city, budget=budget_str, adults=adults)
                if recs:
                    plan["hotel_recs"] = recs
                    updated = True
            except Exception:
                pass

        if not plan.get("tagline"):
            try:
                from bot.handlers.trip_flow import _llm_plan_tagline
                city = plan.get("city", "")
                custom = plan.get("custom", "")
                days_text = plan.get("days_text", "")
                days = int(days_text.replace("天", "").split("天")[0]) if "天" in days_text else 3
                adults = plan.get("adults", 1)
                depart = plan.get("date_display", "")
                tagline = _llm_plan_tagline(city, custom, days, adults, depart)
                if tagline:
                    plan["tagline"] = tagline
                    updated = True
            except Exception:
                pass

        if updated:
            try:
                import json as _json
                from bot.services.redis_store import redis_set
                redis_set(f"download:{token}", _json.dumps(plan, ensure_ascii=False), ttl=259200)
            except Exception:
                pass

        try:
            html = render_plan_html(plan)
        except Exception as e:
            self._err(500, str(e))
            return

        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code: int, msg: str):
        body = msg.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
