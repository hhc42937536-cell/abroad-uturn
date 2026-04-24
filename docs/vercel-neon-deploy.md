# Vercel + Neon PostgreSQL Deploy

This is the recommended production setup.

## Production Cutover Checklist

Use this order for the first production launch:

1. Create Neon and copy the pooled PostgreSQL connection string.
2. Create/import the Vercel project and set production environment variables.
3. Deploy once to get the final `https://*.vercel.app` URL.
4. Set `APP_BASE_URL` to that final URL in Vercel and redeploy.
5. Run the Neon migration from a trusted local terminal.
6. Run deploy checks against the production URL.
7. Configure the LINE webhook and rich menu.
8. Test with one real LINE user before enabling any optional price push.

Keep `ENABLE_PRICE_PUSH=false` for launch unless you are intentionally testing one-to-one tracked-route notifications.

## 1. Create Neon

1. Open Neon and create a new project.
2. Copy the pooled connection string.
3. Use the connection string as `DATABASE_URL`.

The URL should look similar to:

```text
postgresql://user:password@host.neon.tech/dbname?sslmode=require
```

Use the pooled URL for Vercel serverless functions. Keep `sslmode=require`.

## 2. Set Vercel Environment Variables

Required:

```text
DATABASE_URL=
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
APP_BASE_URL=https://your-project.vercel.app
TRAVELPAYOUTS_TOKEN=
TP_MARKER=
```

Optional:

```text
REDIS_URL=
EXCHANGERATE_API_KEY=
GOOGLE_MAPS_API_KEY=
SKYSCANNER_API_KEY=
APIFY_TOKEN=
```

Fare refresh:

```text
ENABLE_FARE_REFRESH=true
FARE_REFRESH_ORIGINS=TPE
FARE_UPDATE_CRON=0 9 * * 1,3,5
FARE_UPDATE_TIMEZONE=Asia/Taipei
ENABLE_PRICE_PUSH=false
PRICE_CHECK_CRON=15 9 * * 1,3,5
```

Notes:

- Vercel Cron schedules in `vercel.json` are UTC. The current production cron runs at 01:00 and 01:15 UTC, which is 09:00 and 09:15 Asia/Taipei.
- The `FARE_UPDATE_CRON` and `PRICE_CHECK_CRON` env vars are used by the long-running Node server mode. Vercel serverless mode uses `vercel.json`.
- `/api/price-check` skips work unless `ENABLE_PRICE_PUSH=true`.

Keep this off unless needed:

```text
LLM_INPUT_NORMALIZATION=false
```

### Vercel CLI Option

If using CLI:

```bash
npm install
npx vercel login
npx vercel link
npx vercel env add DATABASE_URL production
npx vercel env add LINE_CHANNEL_ACCESS_TOKEN production
npx vercel env add LINE_CHANNEL_SECRET production
npx vercel env add OPENAI_API_KEY production
npx vercel env add OPENAI_MODEL production
npx vercel env add APP_BASE_URL production
npx vercel env add TRAVELPAYOUTS_TOKEN production
npx vercel env add TP_MARKER production
npx vercel env add ENABLE_FARE_REFRESH production
npx vercel env add FARE_REFRESH_ORIGINS production
npx vercel env add FARE_UPDATE_TIMEZONE production
npx vercel env add ENABLE_PRICE_PUSH production
npx vercel --prod
```

If using the Vercel dashboard, add the same keys under Project Settings -> Environment Variables, then deploy from Git.

## 3. Install Dependencies Locally

PostgreSQL migration needs `pg`.

```bash
npm install
```

## 4. Run Database Migration

Set the same `DATABASE_URL` locally, then run:

```bash
npm run db:migrate
```

PowerShell example:

```powershell
$env:DATABASE_URL="postgresql://user:password@host.neon.tech/dbname?sslmode=require"
npm run db:migrate
```

The migration is idempotent and creates users, sessions, itineraries, API cache, star events, and price tracking tables.

## 5. Deploy to Vercel

Deploy the project with Vercel.

After deployment, confirm:

```text
https://your-project.vercel.app/health
https://your-project.vercel.app/ready
```

Expected `/ready` signals:

```json
{
  "ok": true,
  "runtime": "vercel",
  "storage": "postgresql",
  "line": true,
  "openai": true,
  "appBaseUrl": true,
  "travelpayouts": true
}
```

## 6. Configure LINE

Set:

```text
APP_BASE_URL=https://your-project.vercel.app
```

Then run:

```bash
npm run line:setup
```

The LINE webhook URL will be:

```text
https://your-project.vercel.app/webhook
```

This command:

- Sets the LINE webhook endpoint.
- Creates the rich menu.
- Uploads `assets/rich-menu.png`.
- Links the rich menu as the default for all users.

If the LINE script fails with a token or permission error, verify that the token is the Messaging API channel access token from the same LINE channel that owns the webhook.

## 7. Verify

Run:

```bash
npm run deploy:check
npm run policy:limited-push
npm run test:vercel-api
```

Production URL checks:

```bash
curl https://your-project.vercel.app/health
curl https://your-project.vercel.app/ready
curl -X POST https://your-project.vercel.app/api/fare-refresh
curl -X POST https://your-project.vercel.app/api/price-check
```

When `ENABLE_PRICE_PUSH=false`, `/api/price-check` should return a skipped response instead of processing tracks.

Final LINE checks:

1. In LINE Developers, press Verify for the webhook URL.
2. Add/follow the bot with one real LINE account.
3. Confirm the onboarding message appears.
4. Tap each Rich Menu area M1-M9 once.
5. Test M3 and confirm fares return.
6. Keep broadcast, multicast, and narrowcast unused.

## Notes

- Vercel memory is not persistent.
- Neon PostgreSQL stores users, sessions, itineraries, API cache, and fare snapshots.
- Broadcast, multicast, and narrowcast are not used.
- Price tracking push is optional and only enabled when `ENABLE_PRICE_PUSH=true`.
- Fare comparison appears only when the user checks M3.
