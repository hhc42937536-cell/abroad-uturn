import { runPriceCheckNow } from '../src/jobs/priceCheckJob.js';
import { env } from '../src/config/env.js';
import { methodNotAllowed, sendJson } from './_http.js';

export default async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST') return methodNotAllowed(res);

  try {
    if (!env.ENABLE_PRICE_PUSH) {
      return sendJson(res, 200, { ok: true, skipped: true, reason: 'price push disabled' });
    }
    const results = await runPriceCheckNow();
    return sendJson(res, 200, {
      ok: true,
      checked: results.length,
      dropped: results.filter((item) => item.dropped).length
    });
  } catch (error) {
    console.error(error);
    return sendJson(res, 500, { ok: false, error: 'Price check failed' });
  }
}
