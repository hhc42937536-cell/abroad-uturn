"""
LINE Bot Webhook -- 出國優轉 (AbroadUturn) v2
==============================================
Vercel Serverless Function (Python)
台灣人專屬的 LINE 出國旅程規劃師

核心功能：
  1. 8 步引導式完整旅程規劃
  2. 便宜國外探索（Google Explore 風格）
  3. 多平台機票比價
  4. 價格追蹤通知
  5. 行前須知（簽證、海關、文化、天氣、匯率）
"""

import json
import sys
import os
import traceback
from http.server import BaseHTTPRequestHandler

# 確保 bot/ 模組可被 import（Vercel 部署環境）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.services.line_api import reply_message, verify_signature
from bot.handlers.router import route_text, route_postback, build_welcome_message
from bot.handlers.tracking import check_all_prices
from bot.utils.logging import log_usage


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """健康檢查 + 價格追蹤 Cron"""
        from urllib.parse import urlparse
        parsed = urlparse(self.path)

        if parsed.path == "/api/check_prices":
            result = check_all_prices()
            self._json_response(200, result)
        elif parsed.path == "/api/refresh_trending":
            from bot.services.trending import refresh_all
            result = refresh_all()
            self._json_response(200, result)
        else:
            self._json_response(200, {"status": "ok", "bot": "AbroadUturn", "version": "2.4", "build": "fix-8fd8b2c"})

    def do_POST(self):
        """LINE Webhook"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # 驗證簽名
        signature = self.headers.get("X-Line-Signature", "")
        if not verify_signature(body, signature):
            self.send_response(403)
            self.end_headers()
            return

        # 立即回 200（LINE 要求 1 秒內回應）
        self._json_response(200, {"status": "ok"})

        # 處理事件
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            return

        for event in payload.get("events", []):
            reply_token = event.get("replyToken", "")
            user_id = event.get("source", {}).get("userId", "")

            try:
                event_type = event.get("type", "")

                # Follow 事件（加好友）
                if event_type == "follow":
                    reply_message(reply_token, build_welcome_message())
                    log_usage(user_id, "follow")
                    continue

                # 文字訊息
                if event_type == "message" and event.get("message", {}).get("type") == "text":
                    user_text = event["message"]["text"].strip()
                    messages = route_text(user_text, user_id)
                    reply_message(reply_token, messages)
                    log_usage(user_id, _classify_feature(user_text))
                    continue

                # Postback 事件（步驟導航按鈕）
                if event_type == "postback":
                    data = event.get("postback", {}).get("data", "")
                    if data:
                        messages = route_postback(data, user_id)
                        reply_message(reply_token, messages)
                        log_usage(user_id, "trip_flow")
                    continue

            except Exception as e:
                tb = traceback.format_exc()
                print(f"[webhook] Error: {e}\n{tb}")
                reply_message(reply_token, [{"type": "text", "text":
                    f"\u7cfb\u7d71\u767c\u751f\u932f\u8aa4\uff0c\u8acb\u7a0d\u5f8c\u518d\u8a66 \U0001f64f\n[debug] {type(e).__name__}: {str(e)[:100]}"}])
                log_usage(user_id, "error", is_success=False)

    def _json_response(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def _classify_feature(text: str) -> str:
    if any(kw in text for kw in ("規劃", "開始")):
        return "trip_flow"
    if any(kw in text for kw in ("探索", "便宜")):
        return "explore"
    if any(kw in text for kw in ("比價", "機票")):
        return "compare"
    if "追蹤" in text:
        return "track"
    return "other"
