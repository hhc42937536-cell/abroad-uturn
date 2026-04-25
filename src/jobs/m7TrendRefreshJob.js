import { env } from '../config/env.js';
import { defaultTrendProfiles } from '../modules/m7Trending.js';
import { refreshM7AutoFeed } from '../services/trendAutoFeed.js';

let lastRunKey = '';

export function startM7TrendRefreshJob() {
  if (!env.ENABLE_M7_AUTO_REFRESH) {
    console.log('M7 auto trend refresh job disabled');
    return null;
  }

  const timer = setInterval(() => {
    void runIfDue().catch((error) => console.error('M7 trend refresh failed', error));
  }, 60 * 1000);

  void runIfDue().catch((error) => console.error('M7 trend refresh failed', error));
  console.log(`M7 trend refresh job scheduled: ${env.M7_AUTO_REFRESH_CRON} ${env.M7_AUTO_REFRESH_TIMEZONE}`);
  return timer;
}

export async function runM7TrendRefreshNow() {
  if (!env.ENABLE_M7_AUTO_REFRESH) return { updatedAt: null, cities: {} };
  const feed = await refreshM7AutoFeed(defaultTrendProfiles);
  console.log(`M7 trend feed updated for ${Object.keys(feed.cities || {}).length} cities`);
  return feed;
}

async function runIfDue() {
  const now = zonedNow(env.M7_AUTO_REFRESH_TIMEZONE);
  if (!isDue(now)) return;
  const key = `${now.year}-${now.month}-${now.day}-${now.hour}-${now.minute}`;
  if (key === lastRunKey) return;
  lastRunKey = key;
  await runM7TrendRefreshNow();
}

function isDue(now) {
  const parsed = parseSimpleCron(env.M7_AUTO_REFRESH_CRON);
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
