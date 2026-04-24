import { hasDatabase, query } from '../config/db.js';

const memoryTracks = [];

export async function createPriceTrack(lineUserId, input) {
  if (!hasDatabase) {
    const record = {
      id: crypto.randomUUID(),
      line_user_id: lineUserId,
      origin_airport: input.originAirport,
      destination_airport: input.destinationAirport,
      depart_date: input.departDate ?? null,
      return_date: input.returnDate ?? null,
      last_price_twd: input.lastPriceTwd ?? null,
      enabled: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    memoryTracks.push(record);
    return record;
  }

  const result = await query(
    `INSERT INTO price_tracks
       (line_user_id, origin_airport, destination_airport, depart_date, return_date, last_price_twd)
     VALUES ($1, $2, $3, $4, $5, $6)
     RETURNING *`,
    [lineUserId, input.originAirport, input.destinationAirport, input.departDate, input.returnDate, input.lastPriceTwd]
  );
  return result.rows[0];
}

export async function listEnabledPriceTracks() {
  if (!hasDatabase) return memoryTracks.filter((track) => track.enabled);
  const result = await query('SELECT * FROM price_tracks WHERE enabled = TRUE ORDER BY created_at ASC');
  return result.rows;
}

export async function updatePriceTrack(id, updates) {
  if (!hasDatabase) {
    const record = memoryTracks.find((track) => track.id === id);
    if (!record) return null;
    Object.assign(record, {
      last_price_twd: updates.lastPriceTwd ?? record.last_price_twd,
      enabled: updates.enabled ?? record.enabled,
      updated_at: new Date().toISOString()
    });
    return record;
  }

  const result = await query(
    `UPDATE price_tracks
     SET last_price_twd = COALESCE($2, last_price_twd),
         enabled = COALESCE($3, enabled),
         updated_at = NOW()
     WHERE id = $1
     RETURNING *`,
    [id, updates.lastPriceTwd, updates.enabled]
  );
  return result.rows[0] ?? null;
}
