import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

loadDotEnv();

export const env = {
  NODE_ENV: process.env.NODE_ENV || 'development',
  PORT: numberEnv('PORT', 3000),
  DATABASE_URL: optionalEnv('DATABASE_URL'),
  REDIS_URL: optionalEnv('REDIS_URL'),
  LINE_CHANNEL_ACCESS_TOKEN: optionalEnv('LINE_CHANNEL_ACCESS_TOKEN'),
  LINE_CHANNEL_SECRET: optionalEnv('LINE_CHANNEL_SECRET'),
  OPENAI_API_KEY: optionalEnv('OPENAI_API_KEY'),
  OPENAI_MODEL: process.env.OPENAI_MODEL || 'gpt-4o-mini',
  TRAVELPAYOUTS_TOKEN: optionalEnv('TRAVELPAYOUTS_TOKEN'),
  TP_MARKER: optionalEnv('TP_MARKER'),
  LLM_INPUT_NORMALIZATION: booleanEnv('LLM_INPUT_NORMALIZATION', false),
  ENABLE_FARE_REFRESH: booleanEnv('ENABLE_FARE_REFRESH', true),
  ENABLE_PRICE_PUSH: booleanEnv('ENABLE_PRICE_PUSH', false),
  PRICE_CHECK_CRON: process.env.PRICE_CHECK_CRON || '15 9 * * 1,3,5',
  FARE_REFRESH_ORIGINS: process.env.FARE_REFRESH_ORIGINS || 'TPE',
  FARE_UPDATE_CRON: process.env.FARE_UPDATE_CRON || '0 9 * * 1,3,5',
  FARE_UPDATE_TIMEZONE: process.env.FARE_UPDATE_TIMEZONE || 'Asia/Taipei',
  APP_BASE_URL: optionalEnv('APP_BASE_URL')
};

function loadDotEnv() {
  const path = resolve(process.cwd(), '.env');
  if (!existsSync(path)) return;

  const content = readFileSync(path, 'utf8');
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const index = trimmed.indexOf('=');
    if (index === -1) continue;
    const key = trimmed.slice(0, index).trim();
    const value = unquote(trimmed.slice(index + 1).trim());
    if (!(key in process.env)) process.env[key] = value;
  }
}

function optionalEnv(key) {
  const value = process.env[key];
  return value && value.trim() ? value.trim() : undefined;
}

function booleanEnv(key, fallback) {
  const value = optionalEnv(key);
  if (value === undefined) return fallback;
  return ['1', 'true', 'yes', 'on'].includes(value.toLowerCase());
}

function numberEnv(key, fallback) {
  const value = Number(process.env[key]);
  return Number.isFinite(value) ? value : fallback;
}

function unquote(value) {
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }
  return value;
}
