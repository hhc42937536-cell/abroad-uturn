import { hasDatabase, query } from '../config/db.js';
import { redis } from '../config/redis.js';

const ttlSeconds = 60 * 60 * 2;
const memorySessions = new Map();

export async function getSession(lineUserId) {
  if (!hasDatabase) {
    const session = memorySessions.get(lineUserId);
    if (!session) return null;
    if (session.expires_at < Date.now()) {
      memorySessions.delete(lineUserId);
      return null;
    }
    return session;
  }

  const cacheKey = sessionKey(lineUserId);
  if (redis?.status === 'ready') {
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);
  }

  const result = await query(
    `SELECT line_user_id, module, step, state
     FROM sessions
     WHERE line_user_id = $1 AND expires_at > NOW()`,
    [lineUserId]
  );
  const session = result.rows[0] ?? null;
  if (session && redis?.status === 'ready') {
    await redis.set(cacheKey, JSON.stringify(session), 'EX', ttlSeconds);
  }
  return session;
}

export async function startSession(lineUserId, module, step, state) {
  if (!hasDatabase) {
    memorySessions.set(lineUserId, {
      line_user_id: lineUserId,
      module,
      step,
      state,
      expires_at: Date.now() + ttlSeconds * 1000
    });
    return;
  }

  await query(
    `INSERT INTO sessions (line_user_id, module, step, state, expires_at)
     VALUES ($1, $2, $3, $4, NOW() + INTERVAL '2 hours')
     ON CONFLICT (line_user_id)
     DO UPDATE SET module = $2, step = $3, state = $4, expires_at = NOW() + INTERVAL '2 hours', updated_at = NOW()`,
    [lineUserId, module, step, state]
  );
  await cacheSession({ line_user_id: lineUserId, module, step, state });
}

export async function updateSession(lineUserId, step, state) {
  if (!hasDatabase) {
    const existing = memorySessions.get(lineUserId);
    if (!existing) return;
    memorySessions.set(lineUserId, {
      ...existing,
      step,
      state,
      expires_at: Date.now() + ttlSeconds * 1000
    });
    return;
  }

  const result = await query(
    `UPDATE sessions
     SET step = $2, state = $3, expires_at = NOW() + INTERVAL '2 hours', updated_at = NOW()
     WHERE line_user_id = $1
     RETURNING line_user_id, module, step, state`,
    [lineUserId, step, state]
  );
  if (result.rows[0]) await cacheSession(result.rows[0]);
}

export async function clearSession(lineUserId) {
  if (!hasDatabase) {
    memorySessions.delete(lineUserId);
    return;
  }

  await query('DELETE FROM sessions WHERE line_user_id = $1', [lineUserId]);
  if (redis?.status === 'ready') await redis.del(sessionKey(lineUserId));
}

async function cacheSession(session) {
  if (redis?.status !== 'ready') return;
  await redis.set(sessionKey(session.line_user_id), JSON.stringify(session), 'EX', ttlSeconds);
}

function sessionKey(lineUserId) {
  return `session:${lineUserId}`;
}
