# 出國優轉2 補強規格（供 Codex 實作）

## 目標

將**出國優轉（Python 版）**的四項核心優勢移植到**出國優轉2（Node.js）**，使其可正式上架取代舊版。

---

## 優先順序

1. **[P0] Travelpayouts API 真實機票資料**
2. **[P0] ExchangeRate-API 真實匯率**
3. **[P1] 降價追蹤 + LINE Push 通知**
4. **[P1] 首次加好友 Onboarding 出發機場選擇**

---

## Task 1 — Travelpayouts 真實機票 API

### 問題

`src/services/flightSearch.js` 的 `buildFareRows()` 使用 `simulatedFare()` 計算假價格。

### 做法

**環境變數**：在 `src/config/env.js` 新增：
```js
TRAVELPAYOUTS_TOKEN: optionalEnv('TRAVELPAYOUTS_TOKEN'),
TP_MARKER: optionalEnv('TP_MARKER'),
```

**替換 `flightSearch.js`**：

```
src/services/flightSearch.js 改寫重點：

1. 新增 `callTravelpayoutsApi(endpoint, params)` — fetch 呼叫
   URL: https://api.travelpayouts.com/aviasales/v3/{endpoint}
   params 預設加 currency=twd, token=TRAVELPAYOUTS_TOKEN
   timeout: 10s
   回傳 response.data（陣列）

2. 改寫 `buildFareRows(from, date)` 為 `fetchFareRows(from)`:
   - 有 token → 呼叫 callTravelpayoutsApi('prices_for_dates', {
       origin: from,
       sorting: 'price',
       limit: 50,
       one_way: 'false',
       currency: 'twd'
     })
   - 將 API 回傳的 { destination, price, airline, transfers, duration_to } 
     對應到 { code: destination, city: DESTINATION_NAMES[destination] || destination,
             priceTwd: price, duration: formatDuration(duration_to),
             stops: transfers === 0 ? '直飛' : `${transfers}轉` }
   - 無 token 或 API 失敗 → fallback 到原本的 popularDestinations 靜態清單 + simulatedFare

3. `refreshFareSnapshot(from)` 改呼叫 `fetchFareRows(from)` 取代 `buildFareRows`

4. 新增 `searchFlightsByRoute(origin, destination, departDate, returnDate)`:
   呼叫 callTravelpayoutsApi('prices_for_dates', {
     origin, destination,
     departure_at: departDate,  // YYYY-MM
     return_at: returnDate,     // YYYY-MM（可選）
     sorting: 'price',
     limit: 30
   })

5. 新增 DESTINATION_NAMES map（IATA code → 中文城市名），至少含：
   NRT/TYO→東京、KIX/OSA→大阪、FUK→福岡、ICN/SEL→首爾、BKK→曼谷、
   SIN→新加坡、KUL→吉隆坡、HKG→香港、SGN/HCM→胡志明市、MNL→馬尼拉、
   DPS→峇里島、NHA→芽莊、DAD→峴港、CTS→札幌、OKA→沖繩

6. bookingUrl 改為 Travelpayouts 聯盟連結（若有 TP_MARKER）：
   https://www.aviasales.com/search/{from}{departCompact}1?marker={TP_MARKER}
   fallback: skyscannerLink（現有邏輯）
```

---

## Task 2 — 真實匯率 API

### 問題

`src/services/exchangeRate.js` 的 `getExchangeRate()` 回傳 `rate: null`。

### 做法

**改寫 `src/services/exchangeRate.js`**（使用免費免 key 的 open.er-api.com）：

```
endpoint: https://open.er-api.com/v6/latest/TWD

1. getExchangeRate(base = 'TWD', target = 'JPY'):
   - withCache(`fx:TWD:${target}`, 43200, async () => {
       const res = await fetch('https://open.er-api.com/v6/latest/TWD')
       const json = await res.json()
       const rate = json.rates[target]
       return buildRateResult(target, rate, json.time_last_update_utc)
     })

2. buildRateResult(currency, rate, dateStr):
   回傳 { rate, currency, display, inverse, example, date }
   - display: `1 TWD = {rate} {currency}` （根據大小決定小數位）
   - inverse: `1 {currency} = X TWD`
   - example: `10,000 TWD ≈ X {currency}`

3. warmPopularCurrencies():
   一次 fetch TWD base，批次更新 JPY/KRW/USD/EUR/THB/SGD/HKD/AUD/VND/PHP/IDR/MYR 到 cache
   供 cron job 呼叫

4. 在 src/jobs/ 新增 exchangeRateWarmJob.js:
   每天 08:00 Asia/Taipei 呼叫 warmPopularCurrencies()
   參考 fareUpdateJob.js 的 cron 結構

5. env.js 新增:
   EXCHANGE_RATE_WARM_CRON: process.env.EXCHANGE_RATE_WARM_CRON || '0 8 * * *'
   ENABLE_EXCHANGE_RATE_WARM: booleanEnv('ENABLE_EXCHANGE_RATE_WARM', true)

6. server.js 啟動時加入 startExchangeRateWarmJob()
```

**相關模組** `src/modules/m4Transport.js`（或現有處理匯率的模組）使用 `getExchangeRate()` 時應處理 rate=null 的情況，顯示「匯率服務暫時不可用」。

---

## Task 3 — 降價追蹤 + LINE Push 通知

### 問題

出國優轉2 明確禁止 push。出國優轉（Python）有完整的追蹤降價 push 功能，是核心差異化。

### 做法

**A. `src/services/line.js` 新增 pushMessage**：
```js
export async function pushMessage(userId, messages) {
  if (!env.LINE_CHANNEL_ACCESS_TOKEN) return;
  const normalized = Array.isArray(messages) ? messages : [messages];
  const response = await fetch('https://api.line.me/v2/bot/message/push', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.LINE_CHANNEL_ACCESS_TOKEN}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify({ to: userId, messages: normalized })
  });
  if (!response.ok) {
    const body = await response.text();
    console.error(`LINE push failed ${response.status}: ${body}`);
  }
}
```

**B. 新增 `src/services/priceTracking.js`**：
```
- addTrack(lineUserId, origin, destination, departDate, returnDate):
  存到 Redis/DB key = `track:{lineUserId}:{origin}_{destination}_{departDate}_{returnDate}`
  value = { origin, destination, departDate, returnDate, lastPriceTwd: 0, createdAt }
  TTL = 30 天

- removeTrack(lineUserId, destinationCode):
  刪除該 user 所有含該 destination 的追蹤

- listUserTracks(lineUserId):
  取得 `track:{lineUserId}:*` 所有追蹤

- checkAllPrices():
  遍歷所有 `track:*` keys
  對每條 track 呼叫 searchFlightsByRoute()（Task 1 新增）
  取最低價，若比 lastPriceTwd 低 5% 以上 → push 通知
  合併每位 user 的所有降價成一則訊息後 push
  格式：
    ✈️ {origin名稱} → {destination名稱}
    📅 {dates}
    💰 NT${old} → NT${new}（省 NT${savings}）
    👉 {bookingUrl}
```

**C. Redis 支援**：`src/services/priceTracking.js` 使用現有 `apiCache.js` 的 `getCachedJson/setCachedJson`，key 前綴用 `track:`。若無 Redis/DB 則直接回傳 not-available。

**D. M3 模組新增追蹤入口**（`src/modules/m3CheapFlights.js`）：
在 `handleStep` 完成顯示後，附帶一個「🔔 追蹤降價」按鈕（Flex Message quick reply），postback action=`track`, value=`{origin}_{destination}_{departDate}` → 呼叫 `addTrack()`

**E. 新增 `src/jobs/priceCheckJob.js`**：
每天 09:00 Asia/Taipei 執行 `checkAllPrices()`
參考 `fareUpdateJob.js` 的 cron 結構

**F. env.js 新增**：
```js
ENABLE_PRICE_TRACKING: booleanEnv('ENABLE_PRICE_TRACKING', true),
PRICE_CHECK_CRON: process.env.PRICE_CHECK_CRON || '0 9 * * *',
```

**G. `src/router/messageRouter.js` 新增取消追蹤指令**：
用戶輸入「取消追蹤 {城市}」→ 呼叫 `removeTrack(lineUserId, destinationCode)`

---

## Task 4 — 首次加好友 Onboarding 出發機場選擇

### 問題

`messageRouter.js` 的 follow 事件只顯示歡迎訊息 + 主選單，沒有詢問出發機場。

### 做法

**改寫 `routeEventInternal` 的 follow 分支**：

```js
if (event.type === 'follow') {
  // 判斷是否新用戶（departure_airport 是否仍是預設 TPE 且 display_name 為 null）
  const user = await getUser(lineUserId);
  const isFirstTime = !user?.display_name; // 或另存 is_onboarded 欄位
  
  const messages = [
    { type: 'text', text: '歡迎使用出國優轉！✈️\n台灣人專屬旅行助理，幫你找最便宜機票、規劃完整行程。' },
    mainMenuFlex()
  ];

  if (isFirstTime) {
    messages.push(buildAirportOnboardingFlex());
  }
  
  return replyMessages(event.replyToken, messages.slice(0, 5));
}
```

**新增 `buildAirportOnboardingFlex()` 在 `src/views/flex/onboarding.js`**：

Flex Message Bubble，footer 有 5 個按鈕：
| 標籤 | postback data |
|------|--------------|
| 🛫 台北桃園 (TPE) | action=set-airport&value=TPE&city=台北 |
| 🛫 台北松山 (TSA) | action=set-airport&value=TSA&city=台北松山 |
| 🛫 高雄小港 (KHH) | action=set-airport&value=KHH&city=高雄 |
| 🛫 台中清泉崗 (RMQ) | action=set-airport&value=RMQ&city=台中 |
| 🛫 台南 (TNN) | action=set-airport&value=TNN&city=台南 |

header: 橘色背景 `#FF6B35`，標題「✈️ 設定出發地」

**`messageRouter.js` 的 normalizeEvent/routeEvent 處理 `action=set-airport`**：
呼叫 `updateUserSettings(lineUserId, { departureAirport: params.get('value'), departureCity: params.get('city') })`
回覆：`✅ 已設定出發地為 {city}（{IATA}），之後搜尋機票都會以此為基礎！`

---

## 需新增的環境變數（.env.example）

```
TRAVELPAYOUTS_TOKEN=     # 機票 API token（aviasales/travelpayouts.com）
TP_MARKER=               # 聯盟佣金 marker（可選）
ENABLE_PRICE_TRACKING=true
PRICE_CHECK_CRON=0 9 * * *
ENABLE_EXCHANGE_RATE_WARM=true
EXCHANGE_RATE_WARM_CRON=0 8 * * *
```

---

## 驗收條件

| 功能 | 驗收條件 |
|------|---------|
| 機票 API | `TRAVELPAYOUTS_TOKEN` 存在時，M3 顯示真實價格；無 token 時顯示 fallback 靜態資料 |
| 匯率 | `getExchangeRate('TWD','JPY')` 回傳非 null rate；無網路時有 fallback |
| 推播 | `checkAllPrices()` 對降價 >5% 的追蹤路線呼叫 `pushMessage()` |
| Onboarding | 新用戶 follow 後收到機場選擇 Flex；選擇後 user 的 departure_airport 更新 |
| 無 token 不崩潰 | 以上所有功能在無任何 token/key 時應 graceful fallback，不拋出 unhandled error |

---

## 注意事項

- 遵循現有架構：服務層放 `src/services/`、排程放 `src/jobs/`、Flex UI 放 `src/views/flex/`
- 所有新 job 在 `src/server.js` 啟動時呼叫 start 函式
- 不要破壞 `npm run policy:reply-only` 的通過（push 只在 cron job 內觸發，不在 webhook reply 流程內）
- 保持 zero external dependencies 精神：fetch 用 Node.js 原生 `fetch`（Node 18+），不加 axios/node-fetch
- Travelpayouts API 加 5 分鐘 in-memory 快取（Map），避免重複呼叫
