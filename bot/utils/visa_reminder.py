"""每週簽證資訊人工核對提醒

透過 LINE push_message 通知管理者
Cron: 每週一 UTC 03:00（台灣時間 11:00）
"""
from __future__ import annotations

import json
import os
import datetime

from bot.config import ADMIN_USER_ID
from bot.services.line_api import push_message

_FLAG_MAP = {
    "JP": "🇯🇵", "KR": "🇰🇷", "TH": "🇹🇭", "SG": "🇸🇬",
    "VN": "🇻🇳", "MY": "🇲🇾", "HK": "🇭🇰", "MO": "🇲🇴",
    "ID": "🇮🇩", "PH": "🇵🇭", "US": "🇺🇸", "GB": "🇬🇧",
    "FR": "🇫🇷", "DE": "🇩🇪", "AU": "🇦🇺", "CA": "🇨🇦",
    "AE": "🇦🇪", "TR": "🇹🇷", "CN": "🇨🇳", "NZ": "🇳🇿",
}

_OFFICIAL_LINKS = {
    "JP": "https://mofa.go.jp/j_info/visit/visa/",
    "KR": "https://visa.go.kr",
    "TH": "https://thaiembassy.org",
    "SG": "https://ica.gov.sg",
    "VN": "https://xuatnhapcanh.gov.vn",
    "MY": "https://imi.gov.my",
    "ID": "https://molina.imigrasi.go.id",
    "PH": "https://dfa.gov.ph",
    "HK": "https://immd.gov.hk",
    "GB": "https://gov.uk/check-uk-visa",
    "US": "https://esta.cbp.dhs.gov",
    "AU": "https://immi.homeaffairs.gov.au",
    "CA": "https://canada.ca",
    "FR": "https://france-visas.gouv.fr",
    "AE": "https://icp.gov.ae",
    "TR": "https://evisa.gov.tr",
}


def send_visa_reminder() -> dict:
    """每週 push 簽證核對提醒給管理者"""
    if not ADMIN_USER_ID:
        print("[visa_reminder] ADMIN_USER_ID 未設定，略過")
        return {"error": "ADMIN_USER_ID not set in Vercel env vars"}

    data_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "visa_info.json")
    )
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            visa_data = json.load(f)
    except Exception as e:
        print(f"[visa_reminder] 讀取失敗: {e}")
        visa_data = {}

    countries = {k: v for k, v in visa_data.items() if k != "_meta"}
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    last_updated = visa_data.get("_meta", {}).get("last_updated", "未知")

    # 第一則：完整清單
    lines = []
    for code, info in countries.items():
        name = info.get("country_name", code)
        is_free = not info.get("visa_required", True)
        status = "✅ 免簽" if is_free else "⚠️ 需簽"
        stay = info.get("stay_limit", "—")
        notes = info.get("notes", "")
        note_short = f"（{notes[:15]}）" if notes else ""
        lines.append(f"{status} {name}・{stay}{note_short}")

    msg1 = (
        f"🛂 每週簽證核對提醒\n"
        f"📅 {today_str}｜上次更新：{last_updated}\n"
        f"共 {len(countries)} 個目的地\n\n"
        + "\n".join(lines)
        + "\n\n"
        "📌 確認：免簽條件/停留天數/入境規定/護照效期\n"
        "如有更新 → 修改 data/visa_info.json → 重新部署"
    )
    push_message(ADMIN_USER_ID, [{"type": "text", "text": msg1}])

    # 第二則：官網連結
    link_lines = ["🔗 各國官方查詢連結："]
    for code, url in _OFFICIAL_LINKS.items():
        if code in countries:
            name = countries[code].get("country_name", code)
            flag = _FLAG_MAP.get(code, "")
            link_lines.append(f"{flag} {name}: {url}")

    push_message(ADMIN_USER_ID, [{"type": "text", "text": "\n".join(link_lines)}])

    print(f"[visa_reminder] 已發送提醒 → {ADMIN_USER_ID[:10]}...，共 {len(countries)} 國")
    return {"sent": True, "countries": len(countries), "date": today_str}
