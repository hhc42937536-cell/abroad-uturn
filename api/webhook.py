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
from bot.config import CRON_SECRET

_CRON_PATHS = {
    "/api/check_prices", "/api/refresh_trending", "/api/warm_exchange",
    "/api/warm_flights", "/api/visa_reminder", "/api/check_policies",
    "/api/check_feedback",
}


def _is_cron_authorized(headers) -> bool:
    """Vercel Cron 會在 Authorization header 帶 Bearer <CRON_SECRET>"""
    if not CRON_SECRET:
        return False
    auth = headers.get("Authorization", "")
    return auth == f"Bearer {CRON_SECRET}"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """健康檢查 + 價格追蹤 Cron"""
        from urllib.parse import urlparse
        parsed = urlparse(self.path)

        if parsed.path in _CRON_PATHS and not _is_cron_authorized(self.headers):
            self.send_response(401)
            self.end_headers()
            return

        if parsed.path == "/api/check_prices":
            result = check_all_prices()
            self._json_response(200, result)
        elif parsed.path == "/api/refresh_trending":
            from bot.services.trending import refresh_all
            result = refresh_all()
            self._json_response(200, result)
        elif parsed.path == "/api/warm_exchange":
            # Cron: 每天 08:00 台灣時間 — 預熱熱門匯率到 Redis
            from bot.services.exchange_api import warm_popular_currencies
            result = warm_popular_currencies()
            self._json_response(200, result)
        elif parsed.path == "/api/warm_flights":
            # Cron: 每天 09:00 台灣時間 — 預取熱門航線到 Redis
            from bot.services.travelpayouts import warm_popular_routes
            result = warm_popular_routes()
            self._json_response(200, result)
        elif parsed.path == "/api/visa_reminder":
            # Cron: 每週一 11:00 台灣時間 — push 簽證核對提醒給開發者
            from bot.utils.visa_reminder import send_visa_reminder
            result = send_visa_reminder()
            self._json_response(200, result)
        elif parsed.path == "/api/check_policies":
            # Cron: 每週一 11:30 台灣時間 — 爬官網偵測簽證/海關政策異動
            from bot.services.policy_checker import run_all_checks
            result = run_all_checks()
            self._json_response(200, result)
        elif parsed.path == "/api/check_feedback":
            # Cron: 每天 09:00 台灣時間 — 推送回程隔天的滿意度問卷
            from bot.utils.feedback import check_and_send_feedback
            result = check_and_send_feedback()
            self._json_response(200, result)
        elif parsed.path == "/api/download":
            # 行程計畫書 .docx 下載
            from urllib.parse import parse_qs
            import json as _json
            from bot.services.redis_store import redis_get
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
            plan = _json.loads(raw)
            from api.download import _build_docx
            content = _build_docx(plan)
            city = plan.get("city", "行程")
            date_display = plan.get("date_display", "").replace("/", "-").replace(" ~ ", "_")
            filename = f"{city}_{date_display}_計畫書.docx"
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
            return
        else:
            self._json_response(200, {"status": "ok", "bot": "AbroadUturn", "version": "2.5", "build": "auto-cron-3x"})

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
                    from bot.services.redis_store import redis_get
                    is_new = not redis_get(f"user:origin:{user_id}")
                    msgs = build_welcome_message()
                    if is_new:
                        msgs = msgs + [_build_onboarding_origin_msg()]
                    reply_message(reply_token, msgs[:5])
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
                        if data.startswith("feedback:"):
                            from bot.utils.feedback import handle_feedback_postback
                            try:
                                score = int(data.split(":")[1])
                                if score < 1 or score > 5:
                                    raise ValueError
                            except (ValueError, IndexError):
                                continue
                            messages = handle_feedback_postback(score, user_id)
                            log_usage(user_id, "feedback")
                        else:
                            messages = route_postback(data, user_id)
                            log_usage(user_id, "trip_flow")
                        reply_message(reply_token, messages)
                    continue

            except Exception as e:
                tb = traceback.format_exc()
                print(f"[webhook] Error: {e}\n{tb}")
                reply_message(reply_token, [{"type": "text", "text":
                    "系統暫時有點忙，請稍後再試一次 🙏\n\n或重新輸入你的目的地，例如「突然想去東京」"}])
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


def _build_onboarding_origin_msg() -> dict:
    """首次加好友：詢問出發機場（onboarding）"""
    return {
        "type": "flex",
        "altText": "✈️ 請問你通常從哪個機場出發？",
        "contents": {
            "type": "bubble", "size": "kilo",
            "header": {
                "type": "box", "layout": "vertical",
                "backgroundColor": "#FF6B35", "paddingAll": "14px",
                "contents": [
                    {"type": "text", "text": "✈️ 設定出發地",
                     "color": "#FFFFFF", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": "讓我更準確找到你的最便宜航班",
                     "color": "#FFE0CC", "size": "xs", "margin": "xs"},
                ],
            },
            "body": {
                "type": "box", "layout": "vertical",
                "paddingAll": "14px", "spacing": "sm",
                "contents": [
                    {"type": "text",
                     "text": "你通常從哪個機場出發？",
                     "weight": "bold", "size": "md"},
                    {"type": "text",
                     "text": "可以之後在「設定」裡隨時更改",
                     "size": "xs", "color": "#999999", "margin": "xs"},
                ],
            },
            "footer": {
                "type": "box", "layout": "vertical",
                "paddingAll": "10px", "spacing": "sm",
                "contents": [
                    {"type": "button", "style": "primary", "color": "#FF6B35", "height": "sm",
                     "action": {"type": "message", "label": "🛫 台北桃園 (TPE)", "text": "出發地 台北"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "🛫 台北松山 (TSA)", "text": "出發地 松山"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "🛫 高雄小港 (KHH)", "text": "出發地 高雄"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "🛫 台中清泉崗 (RMQ)", "text": "出發地 台中"}},
                    {"type": "button", "style": "secondary", "height": "sm",
                     "action": {"type": "message", "label": "🛫 台南 (TNN)", "text": "出發地 台南"}},
                ],
            },
        },
    }
