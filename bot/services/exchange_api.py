"""匯率 API（open.er-api.com，免費、免 key、支援 TWD）

資料來源：ExchangeRate-API Open Access
https://www.exchangerate-api.com/docs/free
"""

import json
import urllib.request

from bot.services.redis_store import redis_get, redis_set


def get_exchange_rate(currency_code: str) -> dict | None:
    """
    取得 TWD 對目標貨幣的匯率
    回傳: {"rate": 4.55, "display": "1 TWD = 4.55 JPY", "example": "10,000 TWD ≈ 45,500 JPY"}
    """
    if not currency_code or currency_code == "TWD":
        return None

    currency_code = currency_code.upper()

    cache_key = f"exchange:{currency_code}"
    cached = redis_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            pass

    try:
        # open.er-api.com：免費、免 key、支援 TWD
        url = "https://open.er-api.com/v6/latest/TWD"
        req = urllib.request.Request(url, headers={"User-Agent": "AbroadUturn/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("result") != "success":
            print(f"[exchange] API status: {data.get('result')}")
            return None

        rates = data.get("rates", {})
        rate = rates.get(currency_code)

        if not rate:
            print(f"[exchange] Currency not found: {currency_code}")
            return None

        example_twd = 10000
        example_foreign = rate * example_twd

        # 顯示格式
        if rate >= 100:
            rate_display = f"{rate:.0f}"
            example_display = f"{example_foreign:,.0f}"
        elif rate >= 10:
            rate_display = f"{rate:.1f}"
            example_display = f"{example_foreign:,.0f}"
        elif rate >= 1:
            rate_display = f"{rate:.2f}"
            example_display = f"{example_foreign:,.1f}"
        else:
            rate_display = f"{rate:.4f}"
            example_display = f"{example_foreign:,.2f}"

        # 反向：外幣對 TWD
        inverse = 1 / rate if rate > 0 else 0
        if inverse >= 1:
            inv_display = f"1 {currency_code} = {inverse:.2f} TWD"
        else:
            inv_display = f"100 {currency_code} = {inverse * 100:.1f} TWD"

        result = {
            "rate": rate,
            "currency": currency_code,
            "display": f"1 TWD = {rate_display} {currency_code}",
            "inverse": inv_display,
            "example": f"{example_twd:,} TWD \u2248 {example_display} {currency_code}",
            "date": data.get("time_last_update_utc", "")[:16],
        }

        redis_set(cache_key, json.dumps(result, ensure_ascii=False), ttl=43200)
        return result

    except Exception as e:
        print(f"[exchange] ERROR: {e}")
        return None
