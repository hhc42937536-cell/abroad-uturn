import { runM7TrendRefreshNow } from '../src/jobs/m7TrendRefreshJob.js';
import { env } from '../src/config/env.js';
import { methodNotAllowed, sendJson } from './_http.js';

export default async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST') return methodNotAllowed(res);

  try {
    if (!env.ENABLE_M7_AUTO_REFRESH) {
      return sendJson(res, 200, { ok: true, skipped: true, reason: 'm7 auto refresh disabled' });
    }

    const feed = await runM7TrendRefreshNow();
    return sendJson(res, 200, {
      ok: true,
      updatedAt: feed.updatedAt,
      cityCount: Object.keys(feed.cities || {}).length
    });
  } catch (error) {
    console.error(error);
    return sendJson(res, 500, { ok: false, error: 'M7 trend refresh failed' });
  }
}
