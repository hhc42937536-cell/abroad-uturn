import { getUser } from '../repositories/userRepository.js';
import { exploreCheapFlights } from '../services/flightSearch.js';
import { skyscannerLink } from '../services/deepLinks.js';
import { cardAsk, done, textValue } from './shared.js';

const taiwanAirports = [
  { label: '桃園 TPE', value: 'TPE', city: '台北' },
  { label: '松山 TSA', value: 'TSA', city: '台北' },
  { label: '高雄 KHH', value: 'KHH', city: '高雄' },
  { label: '台中 RMQ', value: 'RMQ', city: '台中' },
  { label: '台南 TNN', value: 'TNN', city: '台南' }
];

export const m3 = {
  async start({ lineUserId }) {
    const user = await getUser(lineUserId);
    const current = user?.departure_airport ?? 'TPE';
    return cardAsk(
      '探索最便宜',
      `選出發機場，我會列出目前最適合衝一波的低價目的地。現在設定：${current}`,
      taiwanAirports.map((airport) => ({
        label: airport.label,
        value: airport.value,
        displayText: `從 ${airport.value} 找便宜機票`
      })),
      1
    );
  },

  async handleStep({ message }) {
    const from = textValue(message).toUpperCase() || 'TPE';
    const flights = await exploreCheapFlights(from);
    return done(flightCarousel(from, flights));
  }
};

function flightCarousel(from, flights) {
  return {
    type: 'flex',
    altText: `${from} 便宜機票推薦`,
    contents: {
      type: 'carousel',
      contents: flights.slice(0, 8).map((flight, index) => ({
        type: 'bubble',
        size: 'micro',
        body: {
          type: 'box',
          layout: 'vertical',
          spacing: 'sm',
          contents: [
            { type: 'text', text: `${index + 1}. ${flight.city}`, weight: 'bold', size: 'lg', wrap: true },
            { type: 'text', text: `${from} -> ${flight.code}`, color: '#2563eb', size: 'sm' },
            { type: 'text', text: `TWD ${flight.priceTwd.toLocaleString()} 起`, weight: 'bold', size: 'md', color: '#dc2626' },
            { type: 'text', text: `${flight.duration} / ${flight.stops}`, size: 'xs', color: '#6b7280' },
            { type: 'text', text: comparisonText(flight), size: 'xs', color: flight.isCheaperThanLastWeek ? '#059669' : '#6b7280', wrap: true }
          ]
        },
        footer: {
          type: 'box',
          layout: 'vertical',
          spacing: 'sm',
          contents: [
            {
              type: 'button',
              style: 'primary',
              height: 'sm',
              action: {
                type: 'uri',
                label: '直接查機票',
                uri: flight.bookingUrl || skyscannerLink({ from, to: flight.code })
              }
            },
            {
              type: 'button',
              style: 'secondary',
              height: 'sm',
              action: {
                type: 'postback',
                label: '追蹤降價',
                data: `action=track_price&origin=${encodeURIComponent(from)}&destination=${encodeURIComponent(flight.code)}&price=${flight.priceTwd}`,
                displayText: `追蹤 ${flight.code} 降價`
              }
            }
          ]
        }
      }))
    }
  };
}

function comparisonText(flight) {
  if (!flight.previousPriceTwd) return '目前沒有上週比較資料，先看即時價格。';
  if (flight.isCheaperThanLastWeek) return `比上週便宜 TWD ${Math.abs(flight.diffTwd).toLocaleString()}`;
  if (flight.diffTwd > 0) return `比上週貴 TWD ${flight.diffTwd.toLocaleString()}`;
  return '和上週差不多。';
}
