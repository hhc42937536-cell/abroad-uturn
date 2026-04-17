# 出國優轉 LINE Bot — 完整專案說明

## 專案概述

**出國優轉** 是一個專為台灣旅客設計的 LINE Bot，提供從機票比價、行程規劃、簽證資訊到行前準備的一站式出國旅遊助手。

- **語言**：Python
- **部署**：Vercel Serverless Functions
- **資料庫**：Upstash Redis（session + cache）
- **主要外部 API**：LINE Messaging API、Travelpayouts、ExchangeRate-API
- **Affiliate 模式**：所有訂票連結內嵌 `abroaduturn` 追蹤碼

---

## 目錄結構

```
出國優轉/
├── api/
│   ├── webhook.py          # LINE Webhook 主入口 + Cron Job 調度
│   └── download.py         # 行程計畫書 .docx 產生器
├── bot/
│   ├── config.py           # 環境變數集中管理
│   ├── handlers/           # 各功能入口
│   ├── services/           # 外部 API 服務層
│   ├── utils/              # 工具函式
│   ├── flex/               # LINE Flex Message 元件
│   ├── constants/          # 城市/航空公司代碼對照表
│   └── session/            # Redis session 管理
├── data/                   # 靜態 JSON 資料
├── vercel.json             # 部署設定 + Cron 排程
└── requirements.txt        # urllib3, python-docx
```

---

## 核心功能與 Handler

### 1. 完整行程規劃 `trip_flow.py`（8 步驟狀態機）

使用者依序輸入資訊，Bot 帶著走：

| 步驟 | 內容 |
|------|------|
| 1 | 目的地選擇（IATA code 自動補全） |
| 2 | 出發 & 回程日期（date picker） |
| 3 | 旅客人數 & 預算（TWD） |
| 4 | 機票推薦（Travelpayouts API，3-5 個選項） |
| 5 | 住宿推薦（Agoda/Booking.com affiliate） |
| 6 | 每日行程（自動產生天天計畫） |
| 7 | 行前必知（簽證/海關/文化/打包清單） |
| 8 | 摘要 + 下載 .docx 行程計畫書 |

- Session 存於 Redis，TTL 24 小時
- 使用者可隨時「繼續規劃」接續中斷的步驟

---

### 2. 說走就走模式 `quick_trip.py`

無 session 的急速模式：

1. 使用者選天數（2/3/4/5/7 天或自訂）
2. Bot 搜尋最近最便宜的目的地
3. 一鍵產出完整行程卡片

---

### 3. 便宜探索 `explore.py`

多種搜尋模式：
- 最便宜 8 個目的地（from 選定出發地）
- Google Explore 風格泡泡選擇
- 特定航線價格歷史
- 直飛航班篩選
- 彈性日期日曆熱力圖
- 機票 + 飯店套裝
- 熱門目的地排行

---

### 4. 簽證查詢 `visa.py`

- 資料來源：`data/visa_info.json`（40+ 國）
- 台灣護照適用：免簽 / 落地簽 / 電子簽 / 需辦簽
- Redis 可 override（policy_checker 每週自動更新）
- 快速回覆 12 個熱門國家

---

### 5. 機票降價追蹤 `tracking.py`

- 使用者設定追蹤：出發地 → 目的地 + 日期
- Redis 存格式：`track:{user_id}:{route_key}`，TTL 30 天
- Cron 週一/三/五 8am 自動檢查
- 若現價 < 存檔價格，主動 push 通知

---

### 6. 行前必知 `pre_trip.py`

一站整合：
- 簽證需求
- 海關規定
- 文化禮儀
- 打包清單（依季節/目的地）
- 匯率即時查詢

---

### 7. 追星旅遊 `idol_trip.py`

- 資料：`data/idol_events.json`（韓流/日系演唱會/拍攝地）
- 搜尋藝人 → 顯示近期演出日期地點
- 推薦場館附近住宿 & 餐廳

---

### 8. 其他功能

| 功能 | Handler |
|------|---------|
| 住宿搜尋 | `hotels.py`（Agoda/Booking/Trip.com 連結） |
| 交通攻略 | `transport.py`（8 大亞洲城市，捷運卡/APP 指南） |
| 特產手信 | `souvenirs.py`（JP/KR/TH/SG/VN 特色商品） |
| 我的計畫 | `my_plans.py`（查看規劃進度、歷史紀錄） |
| 出發地設定 | `settings.py`（TPE/KHH/RMQ/TNN，TTL 365 天） |

---

## 服務層 Services

### `travelpayouts.py`
- 查詢最便宜航班（月份/特定日期/任意目的地）
- 智慧快取：5 分鐘記憶體 + Redis 6 小時
- Cron 每日 1am 預熱 TPE/KHH/RMQ/TNN 四機場資料
- 無資料時 fallback mock 資料

### `exchange_api.py`
- ExchangeRate-API 即時匯率（TWD → JPY/KRW/USD 等）
- Cron 每日 midnight 預熱常用幣別（Redis 12 小時 TTL）

### `policy_checker.py`
- 每週一 3:30am UTC 自動爬外交部 + 各國海關官網
- 偵測簽證/海關規定異動 → 更新 Redis live data（TTL 8 天）

### `redis_store.py`
- Upstash Redis REST API 封裝（Bearer Token 驗證）
- 支援 SET/GET/KEYS/DEL + TTL

### `travel_data.py`
- 統一資料載入器：優先 Redis live data → fallback JSON
- 記憶體快取 JSON 檔（首次讀取後不再重讀磁碟）

---

## 工具層 Utils

### `budget_estimator.py`
- 40+ 機場的每日費用資料庫（飯店/餐飲/交通/活動）
- 回傳完整費用拆分：機票/住宿/餐飲/交通/活動/合計/人均

### `url_builder.py`
- 產生含 affiliate 追蹤碼的訂票連結
- 支援：Skyscanner / Booking.com / Agoda / Google Flights / Google Explore

### `itinerary_builder.py`
- 依目的地 + 天數自動產生每日行程
- 考量抵達/返程時間、鄰近景點群聚、季節性活動

### `date_parser.py`
- 自然語言日期解析："下週二" / "6/15" / "6月15日"
- 目的地名稱解析："東京" / "Tokyo" / "NRT" → 統一 IATA code

### `visa_reminder.py`
- 每週一主動 push 簽證資料狀態給 ADMIN_USER_ID
- 附上 20+ 官方簽證網站連結供人工核查

---

## Cron 排程（vercel.json）

| 時間 | 任務 | 說明 |
|------|------|------|
| 週一/三/五 8am | check_prices | 機票降價通知 |
| 每日 2am | refresh_trending | 熱門目的地更新 |
| 每日 midnight | warm_exchange | 匯率預熱 |
| 每日 1am | warm_flights | 航班資料預熱 |
| 每週一 3am | visa_reminder | 簽證狀態 admin 通知 |
| 每週一 3:30am | check_policies | 自動爬簽證/海關政策 |

---

## 資料檔案（data/）

| 檔案 | 內容 |
|------|------|
| `visa_info.json` | 40+ 國簽證資訊（台灣護照） |
| `customs_info.json` | 海關規定 + 台灣入境限額 |
| `cultural_notes.json` | 各國文化禮儀、禁忌、節假日 |
| `packing_templates.json` | 季節/目的地打包清單 |
| `itinerary_templates.json` | 3/5/7 天行程範本 |
| `transport_info.json` | 8 大城市交通指南 |
| `souvenirs.json` | 5 國特色商品推薦 |
| `idol_events.json` | 韓日藝人演出 & 拍攝地資料 |

---

## Session 資料結構

```json
{
  "origin": "TPE",
  "destination_code": "NRT",
  "destination_name": "東京",
  "depart_date": "2026-06-15",
  "return_date": "2026-06-20",
  "adults": 2,
  "budget": 50000,
  "selected_flight": {},
  "selected_hotel": {},
  "itinerary": [],
  "started_at": "2026-04-17 14:30",
  "updated_at": "2026-04-17 15:45"
}
```

Redis Keys：
- `planning:{user_id}:data` — session 資料（TTL 24h）
- `planning:{user_id}:step` — 目前步驟 1-8（TTL 24h）
- `track:{user_id}:{route}` — 機票追蹤（TTL 30d）
- `visa:live:{code}` — 即時簽證資料（TTL 8d）
- `customs:live:{code}` — 即時海關資料（TTL 8d）

---

## 架構圖

```
LINE 使用者
    │
    ▼
LINE Webhook Event (POST)
    │
    ▼
Vercel /api/webhook.py
    │
    ├─ router.py → 對應 Handler
    │       ├─ trip_flow.py  (8步驟規劃)
    │       ├─ quick_trip.py (說走就走)
    │       ├─ explore.py    (探索便宜航班)
    │       ├─ visa.py       (簽證查詢)
    │       ├─ tracking.py   (降價追蹤)
    │       └─ ...其他功能
    │
    ├─ Services
    │       ├─ Travelpayouts API (機票)
    │       ├─ ExchangeRate-API (匯率)
    │       └─ Upstash Redis (session/cache)
    │
    └─ LINE Reply API → 回覆使用者

Cron Jobs（背景自動執行）
    ├─ 機票降價通知（週一/三/五）
    ├─ 熱門目的地更新（每日）
    ├─ 匯率/航班資料預熱（每日）
    └─ 簽證政策爬蟲（每週）
```

---

## 環境變數需求

```
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_BOT_ID=
TRAVELPAYOUTS_TOKEN=
UPSTASH_REDIS_URL=
UPSTASH_REDIS_TOKEN=
EXCHANGE_RATE_API_KEY=
ADMIN_USER_ID=
```

---

## 目前狀態（2026-04）

- 核心功能完整實作（行程規劃、機票搜尋、簽證、追蹤、行前準備）
- Vercel 部署就緒，Cron Job 排程完整
- 行程計畫書支援 .docx 格式下載
- 準備上線階段
