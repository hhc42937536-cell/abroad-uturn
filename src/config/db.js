import { env } from './env.js';

let pool = null;
let pgLoadAttempted = false;

export const hasDatabase = Boolean(env.DATABASE_URL);

export async function query(text, params) {
  if (!hasDatabase) {
    throw new Error('DATABASE_URL is not configured');
  }
  const db = await getPool();
  return db.query(text, params);
}

async function getPool() {
  if (pool) return pool;
  if (pgLoadAttempted) throw new Error('pg package is required when DATABASE_URL is set');
  pgLoadAttempted = true;

  const pg = await import('pg').catch(() => null);
  if (!pg) throw new Error('pg package is required when DATABASE_URL is set');

  const { Pool } = pg.default ?? pg;
  pool = new Pool({
    connectionString: env.DATABASE_URL,
    ssl: env.DATABASE_URL?.includes('sslmode=require')
      ? { rejectUnauthorized: false }
      : undefined
  });
  return pool;
}
