import { redis } from '../config/redis.js';
import { getDbCache, setDbCache } from '../repositories/apiCacheRepository.js';

export async function getCachedJson(cacheKey) {
  if (redis?.status === 'ready') {
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);
  }
  return getDbCache(cacheKey);
}

export async function setCachedJson(cacheKey, data, ttlSeconds = 3600) {
  if (redis?.status === 'ready') {
    await redis.set(cacheKey, JSON.stringify(data), 'EX', ttlSeconds);
  }
  await setDbCache(cacheKey, data, ttlSeconds);
}

export async function withCache(cacheKey, ttlSeconds, loader) {
  const cached = await getCachedJson(cacheKey);
  if (cached) return cached;
  const data = await loader();
  await setCachedJson(cacheKey, data, ttlSeconds);
  return data;
}
