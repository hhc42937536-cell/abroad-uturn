import { sendJson } from './_http.js';

export default function handler(_req, res) {
  sendJson(res, 200, { ok: true, service: 'travel-line-bot' });
}
