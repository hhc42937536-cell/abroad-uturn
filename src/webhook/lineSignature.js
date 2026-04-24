import crypto from 'node:crypto';
import { env } from '../config/env.js';

export function isValidLineSignature(req, rawBody) {
  if (!env.LINE_CHANNEL_SECRET) return true;

  const signature = req.headers['x-line-signature'];
  if (!signature) return false;

  const expected = crypto
    .createHmac('sha256', env.LINE_CHANNEL_SECRET)
    .update(rawBody)
    .digest('base64');

  const signatureBuffer = Buffer.from(String(signature));
  const expectedBuffer = Buffer.from(expected);
  return signatureBuffer.length === expectedBuffer.length
    && crypto.timingSafeEqual(signatureBuffer, expectedBuffer);
}
