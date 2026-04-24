import { env } from '../src/config/env.js';
import { hasDatabase } from '../src/config/db.js';
import { sendJson } from './_http.js';

export default function handler(_req, res) {
  sendJson(res, 200, {
    ok: true,
    runtime: 'vercel',
    storage: hasDatabase ? 'postgresql' : 'memory',
    redis: Boolean(env.REDIS_URL),
    line: Boolean(env.LINE_CHANNEL_ACCESS_TOKEN && env.LINE_CHANNEL_SECRET),
    openai: Boolean(env.OPENAI_API_KEY),
    appBaseUrl: Boolean(env.APP_BASE_URL),
    travelpayouts: Boolean(env.TRAVELPAYOUTS_TOKEN),
    fareRefresh: {
      enabled: env.ENABLE_FARE_REFRESH,
      cron: env.FARE_UPDATE_CRON,
      timezone: env.FARE_UPDATE_TIMEZONE
    },
    priceTracking: {
      enabled: env.ENABLE_PRICE_PUSH,
      cron: env.PRICE_CHECK_CRON,
      timezone: env.FARE_UPDATE_TIMEZONE
    }
  });
}
