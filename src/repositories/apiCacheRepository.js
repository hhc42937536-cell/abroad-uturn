import { hasDatabase, query } from '../config/db.js';

const memoryCache = new Map();

export async function getDbCache(cacheKey) {
  if (!hasDatabase) {
    const cached = memoryCache.get(cacheKey);
    if (!cached || cached.expiresAt < Date.now()) return null;
    return cached.data;
  }

  const result = await query(
    'SELECT data FROM api_cache WHERE cache_key = $1 AND expires_at > NOW()',
    [cacheKey]
  );
  return result.rows[0]?.data ?? null;
}

export async function setDbCache(cacheKey, data, ttlSeconds) {
  if (!hasDatabase) {
    memoryCache.set(cacheKey, {
      data,
      expiresAt: Date.now() + ttlSeconds * 1000
    });
    return;
  }

  await query(
    `INSERT INTO api_cache (cache_key, data, expires_at)
     VALUES ($1, $2, NOW() + ($3 || ' seconds')::INTERVAL)
     ON CONFLICT (cache_key)
     DO UPDATE SET data = $2, expires_at = NOW() + ($3 || ' seconds')::INTERVAL`,
    [cacheKey, data, ttlSeconds]
  );
}
