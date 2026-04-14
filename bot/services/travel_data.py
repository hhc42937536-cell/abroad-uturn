"""靜態旅遊資料讀取（簽證、海關、文化、打包清單）"""
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
    data = _load_json("visa_info.json")
    return data.get(country_code)


def get_customs_info(country_code: str) -> dict | None:
    data = _load_json("customs_info.json")
    info = data.get(country_code)
    taiwan_return = data.get("_taiwan_return")
    if info and taiwan_return:
        info["taiwan_return"] = taiwan_return
    return info


def get_cultural_notes(country_code: str) -> dict | None:
    data = _load_json("cultural_notes.json")
    return data.get(country_code)


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
