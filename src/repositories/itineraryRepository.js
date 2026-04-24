import { hasDatabase, query } from '../config/db.js';

const memoryItineraries = [];

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
