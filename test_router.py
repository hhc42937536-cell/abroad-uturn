"""路由測試：模擬真實用戶的各種輸入，涵蓋無 session / 有 session 兩種狀態"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import unittest.mock as mock
sys.modules.setdefault("upstash_redis", mock.MagicMock())

FAKE_SESSION = {
    "destination_code": "TYO",
    "destination_name": "東京",
    "depart_date": "2026-06-15",
    "return_date": "2026-06-22",
    "adults": 2,
    "budget": "10萬",
    "hotel_pref": "便宜優先",
    "custom_requests": "",
    "origin": "TPE",
}

# ── 無 session 測試 ───────────────────────────────────────
NO_SESSION_CASES = [
    # 自然語言規劃意圖
    "帶我去找邊佑錫",
    "突然想去首爾",
    "我好想出國",
    "好想出去玩",
    "幫我規劃一趟旅行",
    "下個月想出國放鬆一下",
    "想帶老婆去日本",
    "我要去蜜月旅行",
    "想帶小孩出去玩",
    "暑假要出國",
    # 目的地
    "我想去東京",
    "想去韓國",
    "泰國好嗎",
    "新加坡怎麼樣",
    "去歐洲要多少錢",
    "推薦一個便宜的地方",
    "有哪裡便宜可以去",
    # 行前/簽證
    "去日本要簽證嗎",
    "首爾的簽證怎麼辦",
    "出國要帶什麼",
    # 追星
    "我想去看 BTS 演唱會",
    "Snow Man 有活動嗎",
    "追星去韓國",
    # 住宿/交通
    "東京住哪裡好",
    "首爾的飯店",
    "日本要買什麼交通卡",
    # 閒聊/邊界
    "謝謝",
    "好",
    "幫幫我",
    ":)",
    "???",
    "1234",
    "",
    " ",
    "a" * 200,
]

# ── 有 session（step=6 行程偏好步驟）測試 ────────────────
IN_SESSION_CASES = [
    # 正常偏好輸入
    "想去迪士尼",
    "美食為主",
    "幫我規劃",
    # 完全離題的奇怪輸入
    "幫我把極光帶回來",
    "我要買保險",
    "飛機會不會很貴",
    "我不知道耶",
    "隨便",
    # 應該觸發跳脫提示的
    "追星 BTS",
    "行前必知",
    "便宜的地方",
    "住宿推薦",
    "交通卡",
    # 取消/繼續
    "取消規劃",
    "繼續規劃",
]


def run_tests():
    passed = failed = 0
    failures = []

    import bot.handlers.router as router_mod
    original_llm = router_mod._llm_intent_fallback
    router_mod._llm_intent_fallback = lambda t, u: router_mod._static_fallback()

    print("=" * 55)
    print("[A] 無 session 測試")
    print("=" * 55)

    with mock.patch("bot.session.manager.get_session", return_value=None), \
         mock.patch("bot.session.manager.get_step", return_value=0), \
         mock.patch("bot.services.redis_store.redis_get", return_value=None), \
         mock.patch("bot.services.redis_store.redis_set", return_value=None), \
         mock.patch("bot.handlers.settings.get_user_origin", return_value="TPE"), \
         mock.patch("bot.services.scraper.scrape_idol_events", return_value=[]), \
         mock.patch("bot.services.exchange_api.get_exchange_rate", return_value=None), \
         mock.patch("bot.services.travelpayouts.search_flights", return_value=[]):
        from bot.handlers.router import route_text
        for text in NO_SESSION_CASES:
            try:
                result = route_text(text, "test_user")
                assert isinstance(result, list) and len(result) > 0
                passed += 1
                print(f"  [OK] {repr(text[:40])}")
            except Exception as e:
                failed += 1
                failures.append(("no-session", text, type(e).__name__, str(e)[:80]))
                print(f"  [FAIL] {repr(text[:40])} => {e}")

    print()
    print("=" * 55)
    print("[B] 有 session（step=6）測試")
    print("=" * 55)

    with mock.patch("bot.session.manager.get_session", return_value=FAKE_SESSION), \
         mock.patch("bot.session.manager.get_step", return_value=6), \
         mock.patch("bot.session.manager.update_session"), \
         mock.patch("bot.session.manager.clear_session"), \
         mock.patch("bot.utils.itinerary_builder.build_itinerary_flex", return_value=[]), \
         mock.patch("bot.services.redis_store.redis_get", return_value=None), \
         mock.patch("bot.services.redis_store.redis_set", return_value=None), \
         mock.patch("bot.handlers.settings.get_user_origin", return_value="TPE"), \
         mock.patch("bot.services.scraper.scrape_idol_events", return_value=[]), \
         mock.patch("bot.services.exchange_api.get_exchange_rate", return_value=None), \
         mock.patch("bot.services.travelpayouts.search_flights", return_value=[]):
        import importlib
        import bot.handlers.router as r2
        importlib.reload(r2)
        r2._llm_intent_fallback = lambda t, u: r2._static_fallback()
        for text in IN_SESSION_CASES:
            try:
                result = r2.route_text(text, "test_user")
                assert isinstance(result, list) and len(result) > 0
                passed += 1
                print(f"  [OK] {repr(text[:40])}")
            except Exception as e:
                failed += 1
                failures.append(("in-session", text, type(e).__name__, str(e)[:80]))
                print(f"  [FAIL] {repr(text[:40])} => {e}")

    router_mod._llm_intent_fallback = original_llm

    print()
    print("=" * 55)
    total = len(NO_SESSION_CASES) + len(IN_SESSION_CASES)
    print(f"結果：{passed}/{total} 通過，{failed} 失敗")
    if failures:
        print("\n失敗清單：")
        for ctx, text, etype, emsg in failures:
            print(f"  [{ctx}] {repr(text[:40])}")
            print(f"         {etype}: {emsg}")
    return failed


if __name__ == "__main__":
    sys.exit(run_tests())
