import { env } from './env.js';

export let redis = null;

function createUpstashClient(baseUrl, token) {
  const headers = { Authorization: `Bearer ${token}`, 'content-type': 'application/json' };

  async function cmd(...args) {
    const res = await fetch(baseUrl, { method: 'POST', headers, body: JSON.stringify(args) });
    const json = await res.json();
    if (json.error) throw new Error(json.error);
    return json.result;
  }

  return {
    status: 'ready',
    get: (key) => cmd('GET', key),
    set: (key, value, ex, ttl) => ex === 'EX' ? cmd('SET', key, value, 'EX', String(ttl)) : cmd('SET', key, value),
    del: (key) => cmd('DEL', key),
    keys: (pattern) => cmd('KEYS', pattern),
  };
}

export async function connectRedis() {
  if (redis?.status === 'ready') return;

  if (env.UPSTASH_REDIS_URL && env.UPSTASH_REDIS_TOKEN) {
    redis = createUpstashClient(env.UPSTASH_REDIS_URL, env.UPSTASH_REDIS_TOKEN);
    console.log('Redis: connected via Upstash REST');
    return;
  }

  if (env.REDIS_URL) {
    const mod = await import('ioredis').catch(() => null);
    if (!mod) {
      console.warn('REDIS_URL is set but ioredis is not installed');
      return;
    }
    const Redis = mod.default;
    redis = new Redis(env.REDIS_URL, { maxRetriesPerRequest: 1, lazyConnect: true });
    await redis.connect().catch(() => undefined);
  }
}
