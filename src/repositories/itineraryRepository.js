import { hasDatabase, query } from '../config/db.js';

const memoryItineraries = [];

export async function getLatestItinerary(lineUserId) {
  if (!hasDatabase) {
    return memoryItineraries
      .filter((item) => item.line_user_id === lineUserId)
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0] ?? null;
  }
  const result = await query(
    `SELECT * FROM itineraries WHERE line_user_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [lineUserId]
  );
  return result.rows[0] ?? null;
}

export async function createItinerary(lineUserId, payload) {
  if (!hasDatabase) {
    const itinerary = {
      id: crypto.randomUUID(),
      line_user_id: lineUserId,
      ...payload,
      created_at: new Date().toISOString()
    };
    memoryItineraries.push(itinerary);
    return itinerary;
  }

  const result = await query(
    `INSERT INTO itineraries
       (line_user_id, module, destination, start_date, end_date, traveler_count, budget_twd, content)
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
     RETURNING *`,
    [
      lineUserId,
      payload.module,
      payload.destination,
      payload.startDate,
      payload.endDate,
      payload.travelerCount ?? 1,
      payload.budgetTwd,
      payload.content
    ]
  );
  return result.rows[0];
}
