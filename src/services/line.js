import { env } from '../config/env.js';

export async function replyMessages(replyToken, messages) {
  const normalized = Array.isArray(messages) ? messages : [messages];
  if (!env.LINE_CHANNEL_ACCESS_TOKEN) {
    console.log(JSON.stringify({ replyToken, messages: normalized }, null, 2));
    return;
  }
  const response = await fetch('https://api.line.me/v2/bot/message/reply', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.LINE_CHANNEL_ACCESS_TOKEN}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify({ replyToken, messages: normalized })
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`LINE reply failed ${response.status}: ${body}`);
  }
}

export async function pushMessage(to, messages) {
  const normalized = Array.isArray(messages) ? messages : [messages];
  if (!env.ENABLE_PRICE_PUSH) {
    console.log('Price push skipped because ENABLE_PRICE_PUSH is not true');
    return;
  }
  if (!env.LINE_CHANNEL_ACCESS_TOKEN) {
    console.log(JSON.stringify({ to, messages: normalized }, null, 2));
    return;
  }
  const response = await fetch('https://api.line.me/v2/bot/message/push', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.LINE_CHANNEL_ACCESS_TOKEN}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify({ to, messages: normalized.slice(0, 5) })
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`LINE push failed ${response.status}: ${body}`);
  }
}

export async function getLineProfile(userId) {
  if (!env.LINE_CHANNEL_ACCESS_TOKEN) return null;
  try {
    const response = await fetch(`https://api.line.me/v2/bot/profile/${userId}`, {
      headers: { authorization: `Bearer ${env.LINE_CHANNEL_ACCESS_TOKEN}` }
    });
    if (!response.ok) return null;
    return response.json();
  } catch (error) {
    console.warn('Failed to load LINE profile', error);
    return null;
  }
}

export function replyText(replyToken, text) {
  return replyMessages(replyToken, { type: 'text', text });
}

export function replyFlex(replyToken, flex) {
  return replyMessages(replyToken, flex);
}

export function textMessage(text) {
  return { type: 'text', text };
}
