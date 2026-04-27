"""機場攻略：新手出國機場流程 Flex Carousel"""
from __future__ import annotations


def _step_card(step_num: int, title: str, color: str, icon: str,
               items: list[str], tip: str = "") -> dict:
    """單一步驟卡片"""
    rows = []
    for item in items:
        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "sm", "margin": "sm",
            "contents": [
                {"type": "text", "text": "•", "size": "sm", "color": "#FF6B35",
                 "flex": 0, "gravity": "top"},
                {"type": "text", "text": item, "size": "sm", "color": "#333333",
                 "wrap": True, "flex": 1},
            ],
        })
    if tip:
        rows.append({"type": "separator", "margin": "md"})
        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "sm", "margin": "md",
            "contents": [
                {"type": "text", "text": "💡", "size": "sm", "flex": 0},
                {"type": "text", "text": tip, "size": "xs", "color": "#888888",
                 "wrap": True, "flex": 1},
            ],
        })
    return {
        "type": "bubble", "size": "kilo",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": color, "paddingAll": "14px",
            "contents": [
                {"type": "text", "text": f"STEP {step_num}",
                 "color": "#FFFFFF99", "size": "xs", "weight": "bold"},
                {"type": "text", "text": f"{icon} {title}",
                 "color": "#FFFFFF", "size": "md", "weight": "bold", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical",
            "paddingAll": "14px", "spacing": "xs",
            "contents": rows,
        },
    }


def handle_airport_guide(dest_code: str = "", origin_code: str = "") -> list:
    """回傳機場攻略 Flex Carousel（出發 + 抵達兩段流程）"""
    dest_upper = dest_code.upper() if dest_code else ""
    origin_upper = origin_code.upper() if origin_code else ""

    # ── 依出發機場客製「機場到飯店」資訊 ──
    arrival_transport = {
        "GMP": (
            "金浦機場 → 明洞飯店",
            [
                "出入境大廳找「地鐵入口」",
                "5 號線（紫色）在地下 1 樓，閘口前用 T-money 卡感應",
                "搭到孔德站（공덕역），轉 6 號線（棕色）",
                "忠武路站（충무로역）下車，出口 3 步行 8 分鐘到明洞",
                "全程約 50 分鐘，費用約 1,500 韓元（NT$35）",
            ],
            "不想轉車？叫 Kakao T 計程車，直接輸入飯店名，約 25,000–35,000 韓元（NT$600–850）",
        ),
        "ICN": (
            "仁川機場 → 首爾市區",
            [
                "入境大廳 B1 搭機場鐵路（AREX）",
                "直達列車（직통열차）到首爾站約 43 分鐘，1,500 韓元",
                "一般列車（일반열차）各站都停，約 66 分鐘，900 韓元",
                "首爾站轉 1 號線或 4 號線到明洞",
            ],
            "機場巴士（리무진버스）也可直達明洞，約 70 分鐘，16,000 韓元",
        ),
        "NRT": (
            "成田機場 → 東京市區",
            [
                "成田特快 N'EX 到新宿/渋谷約 90 分鐘，3,070 日元",
                "利木津巴士到主要飯店區，約 60–90 分鐘",
                "京成 Skyliner 到上野 / 日暮里約 41 分鐘，2,570 日元",
            ],
            "建議先在台灣購買 IC 卡（Suica/Pasmo）或在機場自動售票機購買",
        ),
        "HND": (
            "羽田機場 → 東京市區",
            [
                "東京單軌電車到浜松町，再轉 JR 山手線，約 30 分鐘",
                "京急線直通品川站約 13 分鐘，600 日元",
                "利木津巴士到主要飯店區約 30–60 分鐘",
            ],
            "羽田距離市區較近，計程車到新宿約 4,500–6,000 日元",
        ),
    }.get(dest_upper)

    if not arrival_transport:
        arrival_transport = (
            f"機場到市區",
            [
                "入境後在出口找「旅客服務中心 / Information」",
                "詢問前往市區的交通方式",
                "確認飯店是否有提供接駁服務",
            ],
            "在機場換少量當地現金備用，ATM 通常在入境大廳",
        )

    # ── 台灣出發機場行李限制提示 ──
    luggage_tip = "行李限重看你購買的票種（通常 20–23 kg 托運 + 7 kg 手提）。超重費用非常貴，提前在家秤好！"

    bubbles = [
        # STEP 0: 出發前準備
        _step_card(
            0, "出發前準備", "#37474F", "🧳",
            [
                "護照（有效期至少 6 個月）",
                "電子機票（手機存好截圖 + email 備份）",
                "信用卡 / 現金（少量台幣換當地幣）",
                "手機充電器、轉接頭（韓國/日本用台灣插頭可直接用）",
                "行動電源（100Wh 以下才能帶上機）",
                "提前在手機下載：航空公司 App、目的地地圖 App",
            ],
            luggage_tip,
        ),

        # STEP 1: 辦理登機 Check-in
        _step_card(
            1, "辦理登機 Check-in", "#1565C0", "🛫",
            [
                "出發前 2.5 小時抵達機場（國際線）",
                "看大廳「出發資訊」電子看板，找你的航班號碼與航空公司",
                "到對應航空公司的「報到櫃台（Check-in Counter）」排隊",
                "把護照 + 電子機票（手機或列印）交給地勤人員",
                "告知是否要托運行李（地勤會幫你貼行李條並稱重）",
                "拿回護照 + 登機證（Boarding Pass），確認班機號碼、座位、登機門",
            ],
            "找不到櫃台？問機場工作人員「請問 [航空公司] 的 Check-in 在哪裡？」",
        ),

        # STEP 2: 安全檢查 + 出境
        _step_card(
            2, "安全檢查 + 出境查驗", "#6A1B9A", "🛂",
            [
                "找「出境 / Departure / 국제선 출발」指標往前走",
                "安全檢查：把背包、筆電、外套、皮帶全放進 X 光籃子",
                "液體/凝膠：每件 100ml 以下，全部裝進 1 個透明夾鏈袋",
                "身上金屬物品（鑰匙、零錢）全部取出放籃子",
                "出境查驗：走「本國人（ROC/Taiwan）」通道",
                "把護照遞給海關蓋章，或走 e-Gate 自動通關",
            ],
            "✅ e-Gate 快速通關：要先去移民署申請（申辦一次，往後都能用）",
        ),

        # STEP 3: 候機 + 登機
        _step_card(
            3, "候機 + 登機", "#2E7D32", "🚪",
            [
                "過安檢後看登機證上的「Gate（登機門）」號碼",
                "依指標走到對應的登機門等候（提前 30 分鐘到）",
                "聽廣播：先叫頭等/商務/需要協助的旅客，再叫各排號碼",
                "輪到你時，把登機證（手機或紙本）+ 護照給工作人員掃描",
                "找到你的座位號碼（例：23A → 第 23 排靠窗左側）",
                "手提行李放頭頂行李架，貴重物品放腳邊",
            ],
            "找不到座位？直接問空服員「Excuse me, can you help me find seat 23A?」",
        ),

        # STEP 4: 抵達目的地入境
        _step_card(
            4, "抵達目的地 入境", "#AD1457", "🛬",
            [
                "飛機落地後跟著「入境 / Arrivals / 입국」指標走",
                "入境審查：外國人通道（外国人 / Foreigner）排隊",
                "把護照交給當地海關，可能問「旅遊目的」→ 回答「觀光 / Tourism」",
                "領行李：看入境大廳電子看板找你的「航班號碼」對應的行李轉盤",
                "海關申報：沒有超額物品直接走綠色通道「Nothing to Declare」",
                "出關後就是入境大廳，找交通指標前往市區",
            ],
            "行李還沒出來很正常，最慢的也會在 30 分鐘內出現",
        ),

        # STEP 5: 機場到飯店（依目的地）
        _step_card(
            5, arrival_transport[0], "#E65100", "🚇",
            arrival_transport[1],
            arrival_transport[2],
        ),
    ]

    return [
        {
            "type": "text",
            "text": "✈️ 機場完整攻略\n\n從辦理登機到抵達飯店，6 個步驟帶你走完。← 左右滑動",
        },
        {
            "type": "flex",
            "altText": "機場完整攻略 6 步驟",
            "contents": {"type": "carousel", "contents": bubbles},
        },
        {
            "type": "text",
            "text": "❓ 還有其他問題嗎？\n\n輸入「行前必知」查簽證/天氣/匯率\n輸入「開始規劃」完整規劃你的行程",
            "quickReply": {
                "items": [
                    {"type": "action", "action": {
                        "type": "message", "label": "📋 行前必知", "text": "行前必知"}},
                    {"type": "action", "action": {
                        "type": "message", "label": "✈️ 開始規劃", "text": "開始規劃"}},
                ],
            },
        },
    ]
