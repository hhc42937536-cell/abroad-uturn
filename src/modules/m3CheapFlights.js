import { getUser } from '../repositories/userRepository.js';
import { exploreCheapFlights } from '../services/flightSearch.js';
import { ask, done, textValue } from './shared.js';

export const m3 = {
  async start({ lineUserId }) {
    const user = await getUser(lineUserId);
    const city = user?.departure_city ?? '\u53f0\u5317';
    const airport = user?.departure_airport ?? 'TPE';
    return ask(`\u5f9e\u54ea\u88e1\u51fa\u767c\uff1f\u9810\u8a2d\u70ba ${city}\uff08${airport}\uff09\uff0c\u53ef\u76f4\u63a5\u8f38\u5165\u6a5f\u5834\u4e09\u78bc\u3002`, 1);
  },

  async handleStep({ message }) {
    const from = textValue(message).toUpperCase() || 'TPE';
    const flights = await exploreCheapFlights(from);
    return done({
      type: 'text',
      text: flights
        .map((flight, index) => formatFlight(index, flight))
        .join('\n\n'),
      quickReply: {
        items: flights.slice(0, 5).map((flight) => ({
          type: 'action',
          action: {
            type: 'postback',
            label: `\u8ffd\u8e64 ${flight.code}`,
            data: `action=track_price&origin=${encodeURIComponent(from)}&destination=${encodeURIComponent(flight.code)}&price=${flight.priceTwd}`,
            displayText: `\u8ffd\u8e64 ${flight.code} \u964d\u50f9`
          }
        }))
      }
    });
  }
};

function formatFlight(index, flight) {
  const comparison = flight.previousPriceTwd
    ? flight.isCheaperThanLastWeek
      ? `\n\u2b07 \u6bd4\u4e0a\u9031\u4fbf\u5b9c TWD ${Math.abs(flight.diffTwd).toLocaleString()}`
      : flight.diffTwd > 0
        ? `\n\u2b06 \u6bd4\u4e0a\u9031\u8cb4 TWD ${flight.diffTwd.toLocaleString()}`
        : '\n= \u8207\u4e0a\u9031\u76f8\u540c'
    : '\n\u7121\u4e0a\u9031\u6bd4\u8f03\u8cc7\u6599';

  return `${index + 1}. ${flight.city} (${flight.code})\nTWD ${flight.priceTwd.toLocaleString()} \u8d77\uff5c${flight.duration}\uff5c${flight.stops}${comparison}\n${flight.bookingUrl}`;
}
