import { listEnabledPriceTracks, updatePriceTrack } from '../repositories/priceTrackingRepository.js';
import { skyscannerLink } from './deepLinks.js';
import { searchRouteFare } from './flightSearch.js';
import { pushMessage } from './line.js';

const dropThreshold = 0.05;

export async function checkTrackedPrices() {
  const tracks = await listEnabledPriceTracks();
  const results = [];

  for (const track of tracks) {
    const fare = await searchRouteFare({
      origin: track.origin_airport,
      destination: track.destination_airport,
      departDate: track.depart_date,
      returnDate: track.return_date
    });
    if (!fare?.priceTwd) continue;

    const oldPrice = track.last_price_twd;
    const newPrice = fare.priceTwd;
    const dropped = oldPrice && newPrice <= Math.floor(oldPrice * (1 - dropThreshold));

    if (dropped) {
      await pushMessage(track.line_user_id, {
        type: 'text',
        text: [
          '\u6a5f\u7968\u50f9\u683c\u6bd4\u4e0a\u6b21\u4fbf\u5b9c\u4e86\uff01',
          `${track.origin_airport} -> ${track.destination_airport}`,
          `TWD ${oldPrice.toLocaleString()} -> ${newPrice.toLocaleString()}`,
          `\u964d\u5e45\uff1a${Math.round((1 - newPrice / oldPrice) * 100)}%`,
          skyscannerLink({ from: track.origin_airport, to: track.destination_airport })
        ].join('\n')
      });
    }

    await updatePriceTrack(track.id, { lastPriceTwd: newPrice });
    results.push({ id: track.id, oldPrice, newPrice, dropped: Boolean(dropped) });
  }

  return results;
}
