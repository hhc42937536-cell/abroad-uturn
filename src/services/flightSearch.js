import { env } from '../config/env.js';
import { skyscannerLink } from './deepLinks.js';
import { getCachedJson, setCachedJson } from './apiCache.js';

const snapshotTtlSeconds = 60 * 60 * 24 * 14;
const apiBase = 'https://api.travelpayouts.com/aviasales/v3/prices_for_dates';

const destinationMeta = {
  TYO: { city: '\u6771\u4eac', duration: '\u7d043\u5c0f\u6642' },
  NRT: { city: '\u6771\u4eac', duration: '\u7d043\u5c0f\u6642' },
  HND: { city: '\u6771\u4eac', duration: '\u7d043\u5c0f\u6642' },
  SEL: { city: '\u9996\u723e', duration: '\u7d042.5\u5c0f\u6642' },
  ICN: { city: '\u9996\u723e', duration: '\u7d042.5\u5c0f\u6642' },
  GMP: { city: '\u9996\u723e', duration: '\u7d042.5\u5c0f\u6642' },
  BKK: { city: '\u66fc\u8c37', duration: '\u7d044\u5c0f\u6642' },
  KUL: { city: '\u5409\u9686\u5761', duration: '\u7d044.5\u5c0f\u6642' },
  MNL: { city: '\u99ac\u5c3c\u62c9', duration: '\u7d042\u5c0f\u6642' },
  SGN: { city: '\u80e1\u5fd7\u660e\u5e02', duration: '\u7d043.5\u5c0f\u6642' },
  HKG: { city: '\u9999\u6e2f', duration: '\u7d042\u5c0f\u6642' },
  SIN: { city: '\u65b0\u52a0\u5761', duration: '\u7d044.5\u5c0f\u6642' },
  OSA: { city: '\u5927\u962a', duration: '\u7d042.8\u5c0f\u6642' },
  KIX: { city: '\u5927\u962a', duration: '\u7d042.8\u5c0f\u6642' },
  FUK: { city: '\u798f\u5ca1', duration: '\u7d042.3\u5c0f\u6642' },
  DPS: { city: '\u5df4\u5398\u5cf6', duration: '\u7d045.5\u5c0f\u6642' }
};

const fallbackDestinations = ['TYO', 'SEL', 'BKK', 'KUL', 'MNL', 'SGN', 'HKG', 'SIN', 'OSA', 'FUK'];

export async function exploreCheapFlights(from) {
  const snapshot = await getOrCreateFareSnapshot(from);
  return snapshot.current.map((item) => {
    const previous = snapshot.previous?.find((old) => old.code === item.code);
    const diffTwd = previous ? item.priceTwd - previous.priceTwd : 0;
    return {
      ...item,
      from,
      previousPriceTwd: previous?.priceTwd ?? null,
      diffTwd,
      isCheaperThanLastWeek: diffTwd < 0,
      bookingUrl: skyscannerLink({ from, to: item.code })
    };
  });
}

export async function refreshFareSnapshot(from = 'TPE') {
  const cacheKey = fareSnapshotKey(from);
  const existing = await getCachedJson(cacheKey);
  const current = await fetchTravelpayoutsExplore(from).catch((error) => {
    console.error('Travelpayouts fallback', error);
    return buildFallbackFareRows(from, new Date());
  });
  const snapshot = {
    from,
    refreshedAt: new Date().toISOString(),
    provider: env.TRAVELPAYOUTS_TOKEN ? 'travelpayouts' : 'fallback',
    previous: existing?.current ?? null,
    current
  };
  await setCachedJson(cacheKey, snapshot, snapshotTtlSeconds);
  return snapshot;
}

export async function searchRouteFare({ origin, destination, departDate, returnDate = '' }) {
  const rows = await fetchTravelpayoutsPrices({
    origin,
    destination,
    departureAt: departDate?.slice(0, 7) || nextMonth(),
    returnAt: returnDate?.slice(0, 7),
    limit: 10
  }).catch(() => []);
  const best = normalizeTravelpayoutsRows(origin, rows)[0];
  return best ?? buildFallbackFareRows(origin, new Date()).find((row) => row.code === destination);
}

async function getOrCreateFareSnapshot(from) {
  const existing = await getCachedJson(fareSnapshotKey(from));
  if (existing) return existing;
  return refreshFareSnapshot(from);
}

async function fetchTravelpayoutsExplore(from) {
  if (!env.TRAVELPAYOUTS_TOKEN) return buildFallbackFareRows(from, new Date());
  const rows = await fetchTravelpayoutsPrices({
    origin: from,
    departureAt: nextMonth(),
    limit: 50,
    sorting: 'price'
  });
  const normalized = normalizeTravelpayoutsRows(from, rows);
  return normalized.length ? normalized.slice(0, 10) : buildFallbackFareRows(from, new Date());
}

async function fetchTravelpayoutsPrices({ origin, destination, departureAt, returnAt, limit = 30, sorting = 'price' }) {
  const params = new URLSearchParams({
    origin,
    currency: 'twd',
    departure_at: departureAt,
    sorting,
    direct: 'false',
    one_way: returnAt ? 'false' : 'true',
    limit: String(limit),
    page: '1',
    token: env.TRAVELPAYOUTS_TOKEN
  });
  if (env.TP_MARKER) params.set('marker', env.TP_MARKER);
  if (destination) params.set('destination', destination);
  if (returnAt) params.set('return_at', returnAt);

  const response = await fetch(`${apiBase}?${params}`, {
    headers: { 'user-agent': 'TravelLineBot/1.0' }
  });
  if (!response.ok) throw new Error(`Travelpayouts ${response.status}`);
  const data = await response.json();
  if (data?.success === false) throw new Error(`Travelpayouts error: ${data.error ?? 'unknown'}`);
  return Array.isArray(data?.data) ? data.data : Object.values(data?.data ?? {});
}

function normalizeTravelpayoutsRows(from, rows) {
  return rows
    .filter((row) => row.destination && Number(row.price ?? row.value) > 0)
    .map((row) => {
      const code = row.destination;
      const meta = destinationMeta[code] ?? { city: code, duration: '-' };
      return {
        code,
        city: meta.city,
        duration: meta.duration,
        stops: Number(row.transfers ?? row.number_of_changes ?? 0) === 0 ? '\u76f4\u98db' : '\u8f49\u6a5f',
        priceTwd: Math.round(Number(row.price ?? row.value)),
        airline: row.airline ?? '',
        departDate: row.departure_at ?? row.depart_date ?? '',
        returnDate: row.return_at ?? row.return_date ?? '',
        foundAt: row.found_at ?? '',
        actual: row.actual ?? null,
        from
      };
    })
    .sort((a, b) => a.priceTwd - b.priceTwd);
}

function buildFallbackFareRows(from, date) {
  return fallbackDestinations.map((code, index) => {
    const meta = destinationMeta[code];
    return {
      code,
      city: meta.city,
      duration: meta.duration,
      stops: '\u76f4\u98db',
      priceTwd: simulatedFare({ from, to: code, index, date }),
      provider: 'fallback'
    };
  });
}

function simulatedFare({ from, to, index, date }) {
  const week = Math.floor(date.getTime() / (1000 * 60 * 60 * 24 * 7));
  const seed = [...`${from}:${to}:${week}`].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return 4200 + index * 850 + (seed % 9) * 180;
}

function nextMonth() {
  const date = new Date();
  date.setUTCMonth(date.getUTCMonth() + 1);
  return date.toISOString().slice(0, 7);
}

function fareSnapshotKey(from) {
  return `fare:snapshot:${from}`;
}
