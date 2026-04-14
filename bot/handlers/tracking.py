"""價格追蹤功能"""

import json
import time

from bot.constants.cities import CITY_CODES, IATA_TO_NAME, TW_AIRPORTS
from bot.config import UPSTASH_REDIS_URL, TRAVELPAYOUTS_TOKEN
from bot.services.redis_store import redis_set, redis_get, redis_keys, redis_del
from bot.services.travelpayouts import search_flights
from bot.services.line_api import push_message
from bot.utils.url_builder import skyscanner_url


def handle_track(user_id: str, data: str) -> list:
    parts = data.split("|")
    if len(parts) < 4:
        return [{"type": "text", "text": "\u8ffd\u8e64\u683c\u5f0f\u932f\u8aa4\uff0c\u8acb\u5f9e\u822a\u73ed\u5361\u7247\u9ede\u300c\u8ffd\u8e64\u964d\u50f9\u901a\u77e5\u300d\u6309\u9215 \U0001f64f"}]

    origin = parts[1]
    dest = parts[2]
    depart = parts[3]
    ret = parts[4] if len(parts) > 4 else ""
    city_name = IATA_TO_NAME.get(dest, dest)

    route_key = f"{origin}_{dest}_{depart}_{ret}"
    track_key = f"track:{user_id}:{route_key}"
    track_data = json.dumps({
        "origin": origin,
        "destination": dest,
        "depart": depart,
        "return": ret,
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "last_price": 0,
    })

    if UPSTASH_REDIS_URL:
        redis_set(track_key, track_data, ttl=86400 * 30)
        return [{"type": "text", "text":
            f"\u2705 \u5df2\u8a2d\u5b9a\u8ffd\u8e64\uff01\n\n"
            f"\U0001f6e9\ufe0f {IATA_TO_NAME.get(origin, origin)} \u2192 {city_name}\n"
            f"\U0001f4c5 {depart}" + (f" ~ {ret}" if ret else "") + "\n\n"
            f"\u6bcf\u5929\u5e6b\u4f60\u67e5\u6700\u4f4e\u50f9\uff0c\u964d\u50f9\u6703\u7acb\u523b\u901a\u77e5\u4f60 \U0001f4b0\n"
            f"\u53d6\u6d88\u8ffd\u8e64\u8acb\u8f38\u5165\u300c\u53d6\u6d88\u8ffd\u8e64 {city_name}\u300d"
        }]
    else:
        return [{"type": "text", "text":
            f"\u26a0\ufe0f \u8ffd\u8e64\u529f\u80fd\u5c1a\u672a\u555f\u7528\uff08\u9700\u8981 Redis \u8a2d\u5b9a\uff09\n\n"
            f"\u4f60\u53ef\u4ee5\u5148\u5132\u5b58\u9019\u500b\u641c\u5c0b\uff1a\n"
            f"{IATA_TO_NAME.get(origin, origin)} \u2192 {city_name}\n"
            f"{depart}" + (f" ~ {ret}" if ret else "")
        }]


def handle_cancel_track(user_id: str, text: str) -> list:
    if not UPSTASH_REDIS_URL:
        return [{"type": "text", "text": "\u8ffd\u8e64\u529f\u80fd\u5c1a\u672a\u555f\u7528"}]

    keys = redis_keys(f"track:{user_id}:*")
    if not keys:
        return [{"type": "text", "text": "\u4f60\u76ee\u524d\u6c92\u6709\u8ffd\u8e64\u4efb\u4f55\u8def\u7dda \U0001f60a"}]

    dest_name = text.replace("\u53d6\u6d88\u8ffd\u8e64", "").strip()
    dest_code = ""
    for name, code in CITY_CODES.items():
        if name in dest_name:
            dest_code = code
            break

    deleted = 0
    for key in keys:
        if dest_code and dest_code not in key:
            continue
        redis_del(key)
        deleted += 1

    if deleted:
        return [{"type": "text", "text": f"\u2705 \u5df2\u53d6\u6d88 {deleted} \u500b\u8ffd\u8e64\u9805\u76ee"}]
    return [{"type": "text", "text": f"\u627e\u4e0d\u5230\u300c{dest_name}\u300d\u7684\u8ffd\u8e64\u9805\u76ee"}]


def handle_my_tracks(user_id: str) -> list:
    if not UPSTASH_REDIS_URL:
        return [{"type": "text", "text": "\u8ffd\u8e64\u529f\u80fd\u5c1a\u672a\u555f\u7528"}]

    keys = redis_keys(f"track:{user_id}:*")
    if not keys:
        return [{"type": "text", "text":
            "\u4f60\u76ee\u524d\u6c92\u6709\u8ffd\u8e64\u4efb\u4f55\u8def\u7dda\n\n"
            "\U0001f4a1 \u5728\u63a2\u7d22\u6216\u6bd4\u50f9\u7d50\u679c\u4e2d\uff0c\u9ede\u300c\U0001f4e2 \u8ffd\u8e64\u964d\u50f9\u901a\u77e5\u300d\u5c31\u80fd\u958b\u59cb\u8ffd\u8e64\uff01"
        }]

    lines = ["\U0001f514 \u4f60\u7684\u8ffd\u8e64\u6e05\u55ae\uff1a\n"]
    for key in keys[:10]:
        data = redis_get(key)
        if data:
            try:
                info = json.loads(data)
                origin_name = IATA_TO_NAME.get(info["origin"], info["origin"])
                dest_name = IATA_TO_NAME.get(info["destination"], info["destination"])
                lines.append(f"\u2708\ufe0f {origin_name} \u2192 {dest_name}")
                lines.append(f"   \U0001f4c5 {info['depart']}" +
                             (f" ~ {info['return']}" if info.get("return") else ""))
                if info.get("last_price"):
                    lines.append(f"   \U0001f4b0 \u6700\u65b0\u50f9: NT${info['last_price']:,}")
                lines.append("")
            except Exception:
                pass

    lines.append("\u8f38\u5165\u300c\u53d6\u6d88\u8ffd\u8e64 \u57ce\u5e02\u540d\u300d\u53ef\u53d6\u6d88")
    return [{"type": "text", "text": "\n".join(lines)}]


def check_all_prices():
    """Cron: 遍歷所有追蹤，檢查價格變化並推播通知"""
    if not UPSTASH_REDIS_URL:
        return {"status": "redis_not_configured"}

    keys = redis_keys("track:*")
    if not keys:
        return {"status": "no_tracks", "count": 0}

    checked = 0
    notified = 0

    for key in keys:
        try:
            data = redis_get(key)
            if not data:
                continue
            info = json.loads(data)

            parts = key.split(":")
            if len(parts) < 3:
                continue
            user_id = parts[1]

            flights = None
            if TRAVELPAYOUTS_TOKEN:
                flights = search_flights(
                    info["origin"], info["destination"],
                    info["depart"], info.get("return", "")
                )

            if not flights:
                continue

            cheapest = min(flights, key=lambda x: x.get("price", 99999))
            new_price = cheapest.get("price", 0)
            old_price = info.get("last_price", 0)
            checked += 1

            info["last_price"] = new_price
            redis_set(key, json.dumps(info), ttl=86400 * 30)

            if old_price > 0 and new_price < old_price * 0.95:
                savings = old_price - new_price
                dest_name = IATA_TO_NAME.get(info["destination"], info["destination"])
                origin_name = IATA_TO_NAME.get(info["origin"], info["origin"])

                push_message(user_id, [{"type": "text", "text":
                    f"\U0001f514 \u964d\u50f9\u901a\u77e5\uff01\n\n"
                    f"\u2708\ufe0f {origin_name} \u2192 {dest_name}\n"
                    f"\U0001f4c5 {info['depart']}" +
                    (f" ~ {info.get('return', '')}" if info.get("return") else "") + "\n\n"
                    f"\U0001f4b0 NT${old_price:,} \u2192 NT${new_price:,}\n"
                    f"\U0001f389 \u7701 NT${savings:,}\uff01\n\n"
                    f"\u9ede\u6211\u67e5\u770b\u2192 {skyscanner_url(info['origin'], info['destination'], info['depart'], info.get('return', ''))}"
                }])
                notified += 1

        except Exception as e:
            print(f"[check_prices] Error for {key}: {e}")

    return {"status": "ok", "checked": checked, "notified": notified}
