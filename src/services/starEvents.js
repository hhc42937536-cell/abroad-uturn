import { withCache } from './apiCache.js';

export async function searchStarEvents(artistName, eventType) {
  return withCache(`star:${artistName}:${eventType}`, 60 * 60 * 6, async () => ({
    artistName,
    eventType,
    events: [],
    note: 'Ticket crawler not configured yet. Add Apify/Bright Data implementation here.'
  }));
}
