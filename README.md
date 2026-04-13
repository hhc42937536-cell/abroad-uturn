# 出國優轉 AbroadUturn

LINE Bot 國外旅遊助理 — Google Explore 風格，從台灣出發找最便宜的機票。

## 功能

- **便宜國外探索** — 一鍵顯示近期最便宜目的地（含稅總價）
- **多平台機票比價** — 輸入城市+日期，即時比價（50+ 城市支援）
- **價格追蹤通知** — 設定路線，降價自動推播
- **Google Flights 整合** — 每張卡片可跳轉 Google Flights 比價
- **出發地設定** — 支援台北/高雄/台中等出發地
- **九宮格 Rich Menu** — 點選即用，不需記指令

## 技術架構

- **後端**: Vercel Serverless Python (BaseHTTPRequestHandler)
- **資料**: [Travelpayouts API](https://www.travelpayouts.com/) (Aviasales)
- **快取**: Upstash Redis (價格追蹤 + 使用者設定)
- **統計**: Supabase (可選)
- **LINE**: Messaging API + Flex Message + Rich Menu

## 專案結構

```
abroad-uturn/
├── api/webhook.py          # 主 handler（所有邏輯）
├── vercel.json             # Vercel 路由設定
├── requirements.txt        # Python 依賴
├── pyproject.toml          # Python 專案設定
├── create_rich_menu.py     # Rich Menu 圖片生成 + LINE 上傳
└── deploy_vercel.py        # Vercel 部署腳本
```

## 部署方式

### 1. 建立 LINE Channel
- 到 [LINE Developers](https://developers.line.biz/) 建立 Messaging API Channel
- 取得 Channel Secret 和 Channel Access Token

### 2. 申請 API
- [Travelpayouts](https://www.travelpayouts.com/) — 機票資料 + 聯盟佣金
- [Upstash](https://upstash.com/) — 免費 Redis（價格追蹤用）

### 3. Vercel 環境變數

| 變數 | 說明 | 必要 |
|---|---|---|
| `LINE_CHANNEL_SECRET` | LINE 簽名驗證 | 必要 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE API 呼叫 | 必要 |
| `TRAVELPAYOUTS_TOKEN` | 機票 API | 必要 |
| `TP_MARKER` | 聯盟佣金標記 | 建議 |
| `UPSTASH_REDIS_URL` | Redis URL | 追蹤功能需要 |
| `UPSTASH_REDIS_TOKEN` | Redis Token | 追蹤功能需要 |
| `SUPABASE_URL` | 統計記錄 | 可選 |
| `SUPABASE_KEY` | 統計記錄 | 可選 |

### 4. 部署
```bash
# 設定環境變數
set VERCEL_TOKEN=你的Token
set VERCEL_PROJECT_ID=你的ProjectID

# 部署
python deploy_vercel.py
```

### 5. 設定 Webhook
LINE Developers Console → Messaging API → Webhook URL:
```
https://你的專案.vercel.app/api/webhook
```

### 6. 上傳 Rich Menu
```bash
python create_rich_menu.py --token 你的LINE_ACCESS_TOKEN
```

## 使用指令

| 輸入 | 功能 |
|---|---|
| `便宜` `最便宜` `探索` | 近期最便宜目的地 |
| `探索最便宜` `選月份` | 選月份探索 |
| `機票比價` | 進入比價模式 |
| `東京 6/15-6/20` | 直接比價（自動偵測） |
| `我的追蹤` | 查看追蹤清單 |
| `取消追蹤 東京` | 取消特定追蹤 |
| `出發地 高雄` | 設定出發機場 |
| `使用教學` | 完整說明 |
