"""簽證政策異動通知

邏輯：
  讀取 Redis policy:last_run（由 check_policies 每週一 11:30 寫入）
  - 有更新（updated 不為空）→ push 異動摘要給管理者
  - 有失敗（failed 不為空） → push 爬取失敗警告給管理者
  - 全部未變動且無失敗     → 靜默，不發任何訊息

Cron: 每週一 UTC 03:00（台灣時間 11:00），比 check_policies（11:30）早 30 分鐘
→ 實際上讀的是「上週」的結果。如需讀當週，可調整為 11:30 之後執行。
"""
from __future__ import annotations

import json

from bot.config import ADMIN_USER_ID
from bot.services.line_api import push_message
from bot.services.redis_store import redis_get

_FLAG_MAP = {
    "JP": "🇯🇵", "KR": "🇰🇷", "TH": "🇹🇭", "SG": "🇸🇬",
    "VN": "🇻🇳", "MY": "🇲🇾", "HK": "🇭🇰", "MO": "🇲🇴",
    "ID": "🇮🇩", "PH": "🇵🇭", "US": "🇺🇸", "GB": "🇬🇧",
    "FR": "🇫🇷", "DE": "🇩🇪", "AU": "🇦🇺", "CA": "🇨🇦",
    "AE": "🇦🇪", "TR": "🇹🇷",
}


def send_visa_reminder() -> dict:
    """讀取上次 check_policies 的結果，有異動或失敗才通知管理者"""
    if not ADMIN_USER_ID:
        print("[visa_reminder] ADMIN_USER_ID 未設定，略過")
        return {"skipped": "ADMIN_USER_ID not set"}

    raw = redis_get("policy:last_run")
    if not raw:
        # 還沒跑過 check_policies，或 Redis 資料過期
        push_message(ADMIN_USER_ID, [{"type": "text", "text":
            "⚠️ 簽證政策檢查\n\n"
            "找不到上次爬蟲的結果（Redis 無 policy:last_run）\n"
            "請確認 check_policies Cron 是否正常執行。"
        }])
        return {"notified": "no_data"}

    try:
        last = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"error": "parse_failed"}

    run_date = last.get("date", "未知")
    visa = last.get("visa", {})
    customs = last.get("customs", {})

    visa_updated = visa.get("updated", [])
    visa_failed = visa.get("failed", [])
    customs_updated = customs.get("updated", [])
    customs_failed = customs.get("failed", [])

    has_changes = bool(visa_updated or customs_updated)
    has_failures = bool(visa_failed or customs_failed)

    # 無異動無失敗 → 靜默
    if not has_changes and not has_failures:
        print(f"[visa_reminder] {run_date} 無異動無失敗，靜默")
        return {"notified": False, "date": run_date}

    messages = []

    # ── 有異動 ──────────────────────────────────────
    if has_changes:
        lines = [f"🔄 政策異動偵測｜{run_date}\n"]
        if visa_updated:
            lines.append("📘 簽證更新：")
            for code in visa_updated:
                flag = _FLAG_MAP.get(code, "")
                lines.append(f"  {flag} {code}")
        if customs_updated:
            lines.append("\n📦 海關規定更新：")
            for code in customs_updated:
                flag = _FLAG_MAP.get(code, "")
                lines.append(f"  {flag} {code}")
        lines.append("\n已自動寫入 Redis，使用者查詢時會看到新資料。")
        messages.append({"type": "text", "text": "\n".join(lines)})

    # ── 有失敗 ──────────────────────────────────────
    if has_failures:
        lines = [f"⚠️ 爬蟲失敗警告｜{run_date}\n"]
        if visa_failed:
            lines.append("簽證爬取失敗：")
            for item in visa_failed:
                code = item.split(":")[0] if ":" in item else item
                flag = _FLAG_MAP.get(code, "")
                lines.append(f"  {flag} {item}")
        if customs_failed:
            lines.append("\n海關爬取失敗：")
            for item in customs_failed:
                code = item.split(":")[0] if ":" in item else item
                flag = _FLAG_MAP.get(code, "")
                lines.append(f"  {flag} {item}")
        lines.append("\n這些國家仍使用 JSON 基準資料作為 fallback。")
        messages.append({"type": "text", "text": "\n".join(lines)})

    for msg in messages:
        push_message(ADMIN_USER_ID, [msg])

    print(f"[visa_reminder] 已通知 → 異動 {len(visa_updated)+len(customs_updated)} 筆，失敗 {len(visa_failed)+len(customs_failed)} 筆")
    return {
        "notified": True,
        "date": run_date,
        "visa_updated": visa_updated,
        "customs_updated": customs_updated,
        "visa_failed": visa_failed,
        "customs_failed": customs_failed,
    }
