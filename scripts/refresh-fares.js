import '../src/config/env.js';
import { getFareRefreshOrigins, runFareRefreshNow } from '../src/jobs/fareUpdateJob.js';
import { refreshFareSnapshot } from '../src/services/flightSearch.js';

const origins = process.argv.slice(2).map((item) => item.trim().toUpperCase()).filter(Boolean);
if (!origins.length) {
  await runFareRefreshNow();
  process.exit(0);
}

const targets = origins.length ? origins : await getFareRefreshOrigins();

for (const origin of targets) {
  const snapshot = await refreshFareSnapshot(origin);
  console.log(`${origin}: refreshed ${snapshot.current.length} fares at ${snapshot.refreshedAt}`);
}
