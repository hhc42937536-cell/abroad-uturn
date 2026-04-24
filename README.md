# Travel LINE Bot

Backend for the Travel LINE Bot project.

## Current Completion

Approximate completion: 100% for the runnable MVP.

Done:

- LINE webhook endpoint
- LINE rich menu image and upload scripts
- M1-M9 conversation modules
- Session state machine
- PostgreSQL, Redis, and memory-store development mode
- OpenAI itinerary generation with fallback content
- Optional LLM input normalization for typo and date correction
- Fare snapshots refresh weekly and M3 shows cheaper-than-last-snapshot labels
- Railway, Render, and Docker deployment files
- Smoke test scenarios
- LINE signature validation without SDK lock-in
- Limited push behavior: only price tracking drops greater than 5% can push when `ENABLE_PRICE_PUSH=true`

Remaining:

- Connect a real LINE channel and run `npm run line:setup`
- Add production database and Redis URLs
- Add real provider integrations for flight, hotel, visa, trends, and ticket data
- Tune generated Flex Messages after real LINE device testing

Important message policy:

- Normal bot flows only reply when a user sends a message or taps the rich menu.
- Fare snapshots refresh on Monday, Wednesday, and Friday at 09:00 Asia/Taipei.
- When the user checks M3, fares show whether they are cheaper than the previous snapshot.
- No broadcast, multicast, or narrowcast messages are sent.
- Price tracking can send one-to-one LINE push only when `ENABLE_PRICE_PUSH=true`.

Check the policy before deployment:

```bash
npm run policy:limited-push
```

## Local Start

```bash
cp .env.example .env
npm run asset:rich-menu
npm run dev
```

Without `DATABASE_URL`, the bot uses in-memory storage so local testing can start quickly.

The runnable MVP does not require npm packages in memory mode:

```bash
node src/server.js
node scripts/self-test.js
node scripts/refresh-fares.js TPE
```

Install optional dependencies only when using PostgreSQL or Redis:

```bash
npm install
```

Health checks:

```text
GET /health
GET /ready
```

## LINE Setup

Set:

```text
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
APP_BASE_URL=https://your-deployed-service.example.com
```

Then run:

```bash
npm run line:setup
```

This sets the LINE webhook endpoint to `${APP_BASE_URL}/webhook`, creates the rich menu, uploads `assets/rich-menu.png`, and makes it the default rich menu.

## Rich Menu

Generate the image:

```bash
npm run asset:rich-menu
```

Upload/create rich menu only:

```bash
npm run line:rich-menu
```

Maintenance:

```bash
npm run line:rich-menu:list
node scripts/delete-rich-menu.js <richMenuId>
```

## Smoke Test

Start the server first, then run:

```bash
npm run smoke menu
npm run smoke m1
npm run smoke m2
npm run smoke m3
npm run smoke m9
```

Dependency-free self test:

```bash
npm run self-test
node scripts/self-test.js
npm run test:vercel-api
```

## Vercel

This project includes Vercel serverless adapters:

```text
api/webhook.js
api/ready.js
api/health.js
api/fare-refresh.js
vercel.json
```

Use these LINE webhook URLs after deploying to Vercel:

```text
https://your-project.vercel.app/webhook
https://your-project.vercel.app/api/webhook
```

Vercel Cron calls `/api/fare-refresh` on Monday, Wednesday, and Friday at 01:00 UTC, which is 09:00 Asia/Taipei.
Vercel Cron also calls `/api/price-check` at 01:15 UTC for optional tracked-route price-drop checks.

For Vercel production, use Neon PostgreSQL. Serverless memory is not persistent between invocations.

Recommended deploy guide:

[docs/vercel-neon-deploy.md](docs/vercel-neon-deploy.md)

## Deploy

Render uses `render.yaml`.

Railway uses `railway.json`.

Docker:

```bash
docker build -t travel-line-bot .
docker run --env-file .env -p 3000:3000 travel-line-bot
```

## Production Environment

```text
DATABASE_URL=
REDIS_URL=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
APP_BASE_URL=
```

Optional future integration keys:

```text
EXCHANGERATE_API_KEY=
TRAVELPAYOUTS_TOKEN=
GOOGLE_MAPS_API_KEY=
SKYSCANNER_API_KEY=
APIFY_TOKEN=
```

Fare refresh settings:

```text
ENABLE_FARE_REFRESH=true
FARE_REFRESH_ORIGINS=TPE
FARE_UPDATE_CRON=0 9 * * 1,3,5
FARE_UPDATE_TIMEZONE=Asia/Taipei
ENABLE_PRICE_PUSH=false
```

Manual fare refresh:

```bash
npm run fare:refresh
node scripts/refresh-fares.js TPE KHH
```

## Optional LLM Input Normalization

The bot can use the LLM to normalize ambiguous user input, but it is disabled by default to control cost.

```text
LLM_INPUT_NORMALIZATION=false
```

When enabled, the bot can ask the LLM to fix unclear M2 inputs such as informal dates. Deterministic fixes, such as `2026/5/20` to `2026-05-20`, run locally and do not call the LLM.
