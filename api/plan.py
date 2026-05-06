"""
GET /api/plan?token=xxx
從 Redis 讀取行程計畫，回傳 JSON 供 uturn-web 預填表單。
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.services.redis_store import redis_get

_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        token = qs.get("token", [""])[0].strip()

        if not token:
            self._json(400, {"error": "missing token"})
            return

        raw = redis_get(f"download:{token}")
        if not raw:
            self._json(404, {"error": "not found or expired"})
            return

        try:
            plan: dict = json.loads(raw)
        except Exception:
            self._json(500, {"error": "invalid data"})
            return

        # 只回傳網站需要的欄位
        payload = {
            "destination": plan.get("city", ""),
            "dest_code":   plan.get("dest_code", ""),
            "dep_date":    plan.get("depart_date", ""),
            "ret_date":    plan.get("return_date", ""),
            "people":      plan.get("adults", 1),
            "budget":      plan.get("budget", ""),
            "style":       plan.get("hotel_pref", ""),
            "days_text":   plan.get("days_text", ""),
            "date_display": plan.get("date_display", ""),
            "llm_itinerary": plan.get("llm_itinerary", ""),
            "itinerary":   plan.get("itinerary", []),
            "insider":     plan.get("insider", ""),
            "must_eat":    plan.get("must_eat", ""),
        }
        self._json(200, payload)

    def _json(self, code: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for k, v in _CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass
