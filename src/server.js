import http from 'node:http';
import { env } from './config/env.js';
import { hasDatabase } from './config/db.js';
import { connectRedis, hasRedisConfig } from './config/redis.js';
import { startFareUpdateJob } from './jobs/fareUpdateJob.js';
import { runM7TrendRefreshNow, startM7TrendRefreshJob } from './jobs/m7TrendRefreshJob.js';
import { startPriceCheckJob } from './jobs/priceCheckJob.js';
import { handleWebhookRequest } from './webhook/lineWebhook.js';
import { isValidLineSignature } from './webhook/lineSignature.js';

const server = http.createServer(async (req, res) => {
  try {
    setCommonHeaders(res);

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const url = new URL(req.url, `http://${req.headers.host}`);

    if (req.method === 'GET' && url.pathname === '/health') {
      return json(res, 200, { ok: true, service: 'travel-line-bot' });
    }

    if (req.method === 'GET' && url.pathname === '/ready') {
      return json(res, 200, {
        ok: true,
        storage: hasDatabase ? 'postgresql' : hasRedisConfig ? 'redis' : 'memory',
        redis: hasRedisConfig,
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
        },
        m7TrendAuto: {
          enabled: env.ENABLE_M7_AUTO_REFRESH,
          cron: env.M7_AUTO_REFRESH_CRON,
          timezone: env.M7_AUTO_REFRESH_TIMEZONE,
          feedUrl: Boolean(env.M7_TREND_FEED_URL)
        }
      });
    }

    if (req.method === 'POST' && url.pathname === '/webhook') {
      const rawBody = await readBody(req);
      if (!isValidLineSignature(req, rawBody)) {
        return json(res, 401, { ok: false, error: 'Invalid LINE signature' });
      }
      const body = rawBody.length ? JSON.parse(rawBody.toString('utf8')) : {};
      const result = await handleWebhookRequest(body);
      return json(res, 200, result);
    }

    if ((req.method === 'GET' || req.method === 'POST') && url.pathname === '/m7-trend-refresh') {
      if (!env.ENABLE_M7_AUTO_REFRESH) {
        return json(res, 200, { ok: true, skipped: true, reason: 'm7 auto refresh disabled' });
      }
      const feed = await runM7TrendRefreshNow();
      return json(res, 200, { ok: true, updatedAt: feed.updatedAt, cityCount: Object.keys(feed.cities || {}).length });
    }

    return json(res, 404, { ok: false, error: 'Not found' });
  } catch (error) {
    console.error(error);
    return json(res, 500, { ok: false, error: 'Internal server error' });
  }
});

await connectRedis();
startFareUpdateJob();
startPriceCheckJob();
startM7TrendRefreshJob();

server.listen(env.PORT, () => {
  console.log(`Travel LINE Bot listening on ${env.PORT}`);
});

function setCommonHeaders(res) {
  res.setHeader('access-control-allow-origin', '*');
  res.setHeader('access-control-allow-methods', 'GET,POST,OPTIONS');
  res.setHeader('access-control-allow-headers', 'content-type,x-line-signature');
  res.setHeader('x-content-type-options', 'nosniff');
  res.setHeader('referrer-policy', 'no-referrer');
}

function json(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}
