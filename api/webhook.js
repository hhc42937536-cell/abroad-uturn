import { handleWebhookRequest } from '../src/webhook/lineWebhook.js';
import { isValidLineSignature } from '../src/webhook/lineSignature.js';
import { methodNotAllowed, parseJsonBody, readRawBody, sendJson } from './_http.js';

export const config = {
  api: {
    bodyParser: false
  }
};

export default async function handler(req, res) {
  if (req.method !== 'POST') return methodNotAllowed(res);

  try {
    const rawBody = await readRawBody(req);
    if (!isValidLineSignature(req, rawBody)) {
      return sendJson(res, 401, { ok: false, error: 'Invalid LINE signature' });
    }
    const body = parseJsonBody(rawBody);
    return sendJson(res, 200, await handleWebhookRequest(body));
  } catch (error) {
    console.error(error);
    return sendJson(res, 500, { ok: false, error: 'Internal server error' });
  }
}
