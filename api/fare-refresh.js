import { runFareRefreshNow } from '../src/jobs/fareUpdateJob.js';
import { env } from '../src/config/env.js';
import { methodNotAllowed, sendJson } from './_http.js';

export default async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST') return methodNotAllowed(res);

  try {
    if (!env.ENABLE_FARE_REFRESH) {
      return sendJson(res, 200, { ok: true, skipped: true, reason: 'fare refresh disabled' });
    }
    const snapshots = await runFareRefreshNow();
    return sendJson(res, 200, {
      ok: true,
      refreshed: snapshots.map((snapshot) => ({
        from: snapshot.from,
        count: snapshot.current.length,
        refreshedAt: snapshot.refreshedAt
      }))
    });
  } catch (error) {
    console.error(error);
    return sendJson(res, 500, { ok: false, error: 'Fare refresh failed' });
  }
}
