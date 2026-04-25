import { env } from '../config/env.js';
import { withCache } from './apiCache.js';
import { getCachedJson } from './apiCache.js';

const CACHE_KEY = 'm7:trend-feed:v1';
export const M7_AUTO_CACHE_KEY = 'm7:auto-feed:v1';

export async function loadTrendProfiles(defaultProfiles) {
  if (env.ENABLE_M7_AUTO_REFRESH) {
    const auto = await getCachedJson(M7_AUTO_CACHE_KEY).catch(() => null);
    if (auto) {
      const autoCities = readFeedCities(auto);
      const profiles = mergeProfiles(defaultProfiles, autoCities);
      return {
        profiles,
        source: 'auto',
        sourceUpdatedAt: readFeedUpdatedAt(auto)
      };
    }
  }

  if (!env.M7_TREND_FEED_URL) {
    return { profiles: defaultProfiles, source: 'built-in' };
  }

  try {
    const feed = await withCache(CACHE_KEY, env.M7_TREND_CACHE_SECONDS, async () =>
      fetchTrendFeed(env.M7_TREND_FEED_URL)
    );

    const feedCities = readFeedCities(feed);
    const profiles = mergeProfiles(defaultProfiles, feedCities);
    return {
      profiles,
      source: 'remote',
      sourceUpdatedAt: readFeedUpdatedAt(feed)
    };
  } catch (error) {
    console.warn('Failed to load M7 trend feed, fallback to built-in profiles', error);
    return { profiles: defaultProfiles, source: 'built-in' };
  }
}

async function fetchTrendFeed(url) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) throw new Error(`M7 trend feed HTTP ${response.status}`);
    return response.json();
  } finally {
    clearTimeout(timeout);
  }
}

function readFeedCities(feed) {
  if (!feed || typeof feed !== 'object') return {};
  if (feed.cities && typeof feed.cities === 'object') return feed.cities;
  return feed;
}

function readFeedUpdatedAt(feed) {
  if (!feed || typeof feed !== 'object') return '';
  return String(feed.updatedAt || feed.updated || '').trim();
}

function mergeProfiles(defaultProfiles, feedCities) {
  const merged = { ...defaultProfiles };

  for (const [rawCity, rawProfile] of Object.entries(feedCities || {})) {
    const city = String(rawCity || '').trim();
    if (!city || !rawProfile || typeof rawProfile !== 'object') continue;
    merged[city] = mergeProfile(merged[city], rawProfile);
  }

  return merged;
}

function mergeProfile(base, incoming) {
  const fallback = base ?? {};
  return {
    ...fallback,
    ...incoming,
    updated: asText(incoming.updated) || fallback.updated || '',
    hotBuys: asList(incoming.hotBuys, fallback.hotBuys),
    hotSpots: asList(incoming.hotSpots, fallback.hotSpots),
    hotPlans: asList(incoming.hotPlans, fallback.hotPlans),
    caution: asList(incoming.caution, fallback.caution),
    mapQuery: asText(incoming.mapQuery) || fallback.mapQuery || '',
    officialLabel: asText(incoming.officialLabel) || fallback.officialLabel || '',
    officialUri: asText(incoming.officialUri) || fallback.officialUri || ''
  };
}

function asText(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function asList(value, fallback = []) {
  if (!Array.isArray(value)) return Array.isArray(fallback) ? fallback : [];
  const normalized = value
    .map((item) => String(item ?? '').trim())
    .filter(Boolean);
  return normalized.length ? normalized : (Array.isArray(fallback) ? fallback : []);
}
