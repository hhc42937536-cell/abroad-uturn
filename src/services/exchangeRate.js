import { withCache } from './apiCache.js';

export async function getExchangeRate(base = 'TWD', target = 'JPY') {
  const normalizedBase = String(base).toUpperCase();
  const normalizedTarget = String(target).toUpperCase();

  return withCache(`fx:${normalizedBase}:${normalizedTarget}`, 60 * 60 * 12, async () => {
    const url = `https://open.er-api.com/v6/latest/${encodeURIComponent(normalizedBase)}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Exchange rate API failed ${response.status}`);
    }
    const data = await response.json();
    const rate = data?.rates?.[normalizedTarget];
    if (typeof rate !== 'number') {
      throw new Error(`Missing exchange rate ${normalizedBase}/${normalizedTarget}`);
    }
    return {
      base: normalizedBase,
      target: normalizedTarget,
      rate,
      provider: 'open.er-api.com',
      updatedAt: data.time_last_update_utc ?? new Date().toISOString()
    };
  }).catch((error) => {
    console.error('Exchange rate fallback', error);
    return {
      base: normalizedBase,
      target: normalizedTarget,
      rate: null,
      provider: 'fallback',
      updatedAt: new Date().toISOString()
    };
  });
}
