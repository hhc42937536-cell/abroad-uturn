"""靜態旅遊資料讀取（簽證、海關、文化、打包清單）

資料優先順序：
  1. Redis 即時資料（policy_checker 爬蟲更新 / 開發者手動覆寫）
  2. 本地 JSON 檔案（部署時的基準值，不會自動更新）
"""
from __future__ import annotations

import json
import os

_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
_cache = {}


def _load_json(filename: str) -> dict:
    if filename in _cache:
        return _cache[filename]
    filepath = os.path.join(_data_dir, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache[filename] = data
        return data
    except Exception as e:
        print(f"[travel_data] Error loading {filename}: {e}")
        return {}


def get_visa_info(country_code: str) -> dict | None:
    # Redis 優先（policy_checker cron 每週自動更新）
    try:
        from bot.services.policy_checker import get_live_visa
        live = get_live_visa(country_code)
        if live:
            return live
    except Exception:
        pass
    # fallback JSON
    return _load_json("visa_info.json").get(country_code)


def get_customs_info(country_code: str) -> dict | None:
    # Redis 優先
    try:
        from bot.services.policy_checker import get_live_customs
        live = get_live_customs(country_code)
        if live:
            taiwan_return = _load_json("customs_info.json").get("_taiwan_return")
            if taiwan_return:
                live["taiwan_return"] = taiwan_return
            return live
    except Exception:
        pass
    # fallback JSON
    data = _load_json("customs_info.json")
    info = data.get(country_code)
    if info:
        info["taiwan_return"] = data.get("_taiwan_return")
    return info


def get_cultural_notes(country_code: str) -> dict | None:
    data = _load_json("cultural_notes.json")
    return data.get(country_code)


def get_insider_tips(dest_code: str) -> dict | None:
    """讀取目的地的在地眉角（票務時機/人潮規律/交通/隱藏景點/省錢技巧）"""
    data = _load_json("insider_tips.json")
    return data.get(dest_code)


def get_restaurants(dest_code: str) -> dict:
    """讀取目的地精選餐廳資料（依類別分類）"""
    # dest_code 可能是 IATA（TYO/SEL）或國家代碼，先直接查，查不到再嘗試映射
    data = _load_json("restaurants.json")
    result = data.get(dest_code)
    if result:
        return result
    # IATA → city mapping
    _iata_map = {
        "NRT": "TYO", "HND": "TYO",
        "KIX": "OSA", "ITM": "OSA",
        "FUK": "FUK",
        "ICN": "SEL", "GMP": "SEL",
        "BKK": "BKK", "DMK": "BKK",
        "SIN": "SIN",
        "DPS": "DPS",
        "HAN": "HAN",
        "SGN": "SGN",
        "KUL": "KUL",
    }
    mapped = _iata_map.get(dest_code)
    return data.get(mapped, {}) if mapped else {}


def get_restaurants_summary(dest_code: str, max_per_cat: int = 2) -> str:
    """
    把餐廳資料整理成 LLM prompt 用的文字摘要。
    格式：【類別】店名（區域）必點：xxx；價位：xxx；秘訣：xxx
    """
    rests = get_restaurants(dest_code)
    if not rests:
        return ""
    lines = []
    for cat, items in rests.items():
        for item in items[:max_per_cat]:
            line = (
                f"【{cat}】{item['name']}（{item['area']}）"
                f"必點：{item['must_order']}；"
                f"價位：{item['price_per_person']}；"
                f"秘訣：{item['tip']}"
            )
            lines.append(line)
    return "\n".join(lines)


def get_packing_list(country_code: str, month: int = 6) -> dict:
    """根據國家和月份產生打包清單"""
    data = _load_json("packing_templates.json")
    base = data.get("base", {})
    climate_map = data.get("climate_map", {})
    country_items = data.get("country_specific", {}).get(country_code, [])

    # 判斷季節
    if 3 <= month <= 5:
        season = "spring"
    elif 6 <= month <= 8:
        season = "summer"
    elif 9 <= month <= 11:
        season = "autumn"
    else:
        season = "winter"

    # 取得氣候類型
    country_climate = climate_map.get(country_code, {})
    climate_type = country_climate.get(season, "temperate")
    climate_items = data.get(climate_type, {}).get("items", [])
    climate_label = data.get(climate_type, {}).get("label", "")

    return {
        "documents": base.get("documents", []),
        "electronics": base.get("electronics", []),
        "essentials": base.get("essentials", []),
        "toiletries": base.get("toiletries", []),
        "climate_items": climate_items,
        "climate_label": climate_label,
        "country_items": country_items,
    }
