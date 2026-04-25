import { methodNotAllowed, parseJsonBody, readRawBody, sendJson } from './_http.js';

export const config = {
  api: {
    bodyParser: false
  }
};

export default async function handler(req, res) {
  if (req.method !== 'POST') return methodNotAllowed(res);

  try {
    const [{ handleWebhookRequest }, { isValidLineSignature }] = await Promise.all([
      import('../src/webhook/lineWebhook.js'),
      import('../src/webhook/lineSignature.js')
    ]);
    const rawBody = await readRawBody(req);
    if (!isValidLineSignature(req, rawBody)) {
      return sendJson(res, 401, { ok: false, error: 'Invalid LINE signature' });
    }
    const body = parseJsonBody(rawBody);
    return sendJson(res, 200, await handleWebhookRequest(body));
  } catch (error) {
    console.error(error);
    const message = error instanceof Error ? error.message : String(error);
    return sendJson(res, 500, { ok: false, error: 'Internal server error', detail: message });
  }
}
