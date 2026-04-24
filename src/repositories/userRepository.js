import { hasDatabase, query } from '../config/db.js';

const memoryUsers = new Map();

export async function ensureUser(lineUserId, profile = {}) {
  if (!hasDatabase) {
    const existing = memoryUsers.get(lineUserId);
    if (existing) return existing;
    const user = {
      line_user_id: lineUserId,
      display_name: profile.displayName ?? null,
      departure_city: '\u53f0\u5317',
      departure_airport: 'TPE',
      preferred_currency: 'TWD',
      language: 'zh-TW',
      default_traveler_count: 1
    };
    memoryUsers.set(lineUserId, user);
    return user;
  }

  const result = await query(
    `INSERT INTO users (line_user_id, display_name)
     VALUES ($1, $2)
     ON CONFLICT (line_user_id)
     DO UPDATE SET updated_at = NOW()
     RETURNING *`,
    [lineUserId, profile.displayName ?? null]
  );
  return result.rows[0];
}

export async function getUser(lineUserId) {
  if (!hasDatabase) return memoryUsers.get(lineUserId) ?? null;

  const result = await query('SELECT * FROM users WHERE line_user_id = $1', [lineUserId]);
  return result.rows[0] ?? null;
}

export async function updateUserSettings(lineUserId, settings) {
  if (!hasDatabase) {
    const user = memoryUsers.get(lineUserId) ?? await ensureUser(lineUserId);
    const updated = {
      ...user,
      departure_city: settings.departureCity ?? user.departure_city,
      departure_airport: settings.departureAirport ?? user.departure_airport,
      preferred_currency: settings.preferredCurrency ?? user.preferred_currency,
      language: settings.language ?? user.language,
      default_traveler_count: settings.defaultTravelerCount ?? user.default_traveler_count
    };
    memoryUsers.set(lineUserId, updated);
    return updated;
  }

  const result = await query(
    `UPDATE users
     SET departure_city = COALESCE($2, departure_city),
         departure_airport = COALESCE($3, departure_airport),
         preferred_currency = COALESCE($4, preferred_currency),
         language = COALESCE($5, language),
         default_traveler_count = COALESCE($6, default_traveler_count),
         updated_at = NOW()
     WHERE line_user_id = $1
     RETURNING *`,
    [
      lineUserId,
      settings.departureCity,
      settings.departureAirport,
      settings.preferredCurrency,
      settings.language,
      settings.defaultTravelerCount
    ]
  );
  return result.rows[0];
}

export async function listDepartureAirports() {
  if (!hasDatabase) {
    return [...new Set([...memoryUsers.values()].map((user) => user.departure_airport).filter(Boolean))];
  }

  const result = await query(
    `SELECT DISTINCT departure_airport
     FROM users
     WHERE departure_airport IS NOT NULL
     ORDER BY departure_airport`
  );
  return result.rows.map((row) => row.departure_airport);
}
