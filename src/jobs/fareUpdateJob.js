import { env } from '../config/env.js';
import { listDepartureAirports } from '../repositories/userRepository.js';
import { refreshFareSnapshot } from '../services/flightSearch.js';

let lastRunKey = '';

export function startFareUpdateJob() {
  if (!env.ENABLE_FARE_REFRESH) {
    console.log('Fare refresh job disabled');
    return null;
  }

  const timer = setInterval(() => {
    void runIfDue().catch((error) => console.error('Fare refresh failed', error));
  }, 60 * 1000);

  void runIfDue().catch((error) => console.error('Fare refresh failed', error));
  console.log(`Fare refresh job scheduled: ${env.FARE_UPDATE_CRON} ${env.FARE_UPDATE_TIMEZONE}`);
  return timer;
}

export async function runFareRefreshNow() {
  const origins = await getFareRefreshOrigins();
  const snapshots = await Promise.all(origins.map((origin) => refreshFareSnapshot(origin)));
  console.log(`Fare refresh updated ${snapshots.length} origin snapshots`);
  return snapshots;
}

export async function getFareRefreshOrigins() {
  const configured = parseOrigins(env.FARE_REFRESH_ORIGINS);
  const userOrigins = await listDepartureAirports();
  return [...new Set([...configured, ...userOrigins])].filter(Boolean);
}

async function runIfDue() {
  const now = zonedNow(env.FARE_UPDATE_TIMEZONE);
  if (!isDue(now)) return;
  const key = `${now.year}-${now.month}-${now.day}-${now.hour}-${now.minute}`;
  if (key === lastRunKey) return;
  lastRunKey = key;
  await runFareRefreshNow();
}

function isDue(now) {
  const parsed = parseSimpleCron(env.FARE_UPDATE_CRON);
  return parsed.minutes.includes(now.minute)
    && parsed.hours.includes(now.hour)
    && parsed.weekdays.includes(now.weekday);
}

function parseSimpleCron(cron) {
  const [minute, hour, , , weekday] = cron.split(' ');
  return {
    minutes: parsePart(minute, 0, 59),
    hours: parsePart(hour, 0, 23),
    weekdays: parsePart(weekday, 0, 6)
  };
}

function parsePart(part, min, max) {
  if (!part || part === '*') return range(min, max);
  return part.split(',').flatMap((item) => {
    const value = Number(item);
    return Number.isInteger(value) ? [value] : [];
  });
}

function range(min, max) {
  return Array.from({ length: max - min + 1 }, (_, index) => min + index);
}

function zonedNow(timeZone) {
  const date = new Date();
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone,
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    hourCycle: 'h23',
    weekday: 'short'
  }).formatToParts(date);
  const value = (type) => parts.find((part) => part.type === type)?.value;
  return {
    year: Number(value('year')),
    month: Number(value('month')),
    day: Number(value('day')),
    hour: Number(value('hour')),
    minute: Number(value('minute')),
    weekday: weekdayNumber(value('weekday'))
  };
}

function weekdayNumber(value) {
  return { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }[value] ?? 0;
}

function parseOrigins(value) {
  return String(value ?? 'TPE')
    .split(',')
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}
