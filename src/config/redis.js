import { env } from './env.js';

export let redis = null;

export async function connectRedis() {
  if (!env.REDIS_URL || redis?.status === 'ready') return;
  const mod = await import('ioredis').catch(() => null);
  if (!mod) {
    console.warn('REDIS_URL is set but ioredis is not installed; using database/memory cache only');
    return;
  }
  const Redis = mod.default;
  redis = new Redis(env.REDIS_URL, { maxRetriesPerRequest: 1, lazyConnect: true });
  await redis.connect().catch(() => undefined);
}
