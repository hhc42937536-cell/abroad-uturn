import '../src/config/env.js';

const required = [
  'DATABASE_URL',
  'LINE_CHANNEL_ACCESS_TOKEN',
  'LINE_CHANNEL_SECRET',
  'OPENAI_API_KEY',
  'APP_BASE_URL',
  'TRAVELPAYOUTS_TOKEN'
];

const recommended = ['TP_MARKER', 'FARE_UPDATE_TIMEZONE', 'PRICE_CHECK_CRON'];

const missing = required.filter((key) => !process.env[key]?.trim());

if (missing.length) {
  console.error(`Missing required production env vars: ${missing.join(', ')}`);
  process.exit(1);
}

if (!process.env.DATABASE_URL.includes('postgres')) {
  console.error('DATABASE_URL does not look like a PostgreSQL/Neon URL.');
  process.exit(1);
}

if (!process.env.APP_BASE_URL.startsWith('https://')) {
  console.error('APP_BASE_URL must be an https URL.');
  process.exit(1);
}

const missingRecommended = recommended.filter((key) => !process.env[key]?.trim());
if (missingRecommended.length) {
  console.warn(`Recommended env vars not set: ${missingRecommended.join(', ')}`);
}

console.log('deploy env ok');
