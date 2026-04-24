import { routeEvent } from '../router/messageRouter.js';

export async function handleWebhookRequest(body) {
  const events = body.events ?? [];
  const results = await Promise.allSettled(events.map(routeEvent));
  for (const result of results) {
    if (result.status === 'rejected') console.error(result.reason);
  }
  return { ok: true };
}

export async function handleWebhook(req, res, next) {
  try {
    res.json(await handleWebhookRequest(req.body));
  } catch (error) {
    next(error);
  }
}
