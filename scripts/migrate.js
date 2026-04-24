import '../src/config/env.js';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

if (!process.env.DATABASE_URL) {
  console.log('DATABASE_URL is not set; skipping migration for memory-store development mode');
  process.exit(0);
}

const pg = await import('pg').catch(() => null);
if (!pg) {
  console.error('The pg package is required for Neon/PostgreSQL migrations. Run npm install first.');
  process.exit(1);
}

const { Pool } = pg.default ?? pg;
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.DATABASE_URL.includes('sslmode=require')
    ? { rejectUnauthorized: false }
    : undefined
});

const sql = await readFile(join(__dirname, '..', 'sql', '001_init.sql'), 'utf8');
await pool.query(sql);
await pool.end();

console.log('Database migration completed');
