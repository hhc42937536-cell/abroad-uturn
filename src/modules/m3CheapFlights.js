import { getUser } from '../repositories/userRepository.js';
import { exploreCheapFlights } from '../services/flightSearch.js';
import { skyscannerLink } from '../services/deepLinks.js';
import { mainMenuFlex } from '../views/flex/mainMenu.js';

export const m3 = {
  async start({ lineUserId }) {
    const user = await getUser(lineUserId);
    const from = user?.departure_airport ?? 'TPE';
    const flights = await exploreCheapFlights(from);
    return { done: true, messages: [flightCarousel(from, flights), mainMenuFlex()] };
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
        header: {
          type: 'box',
          layout: 'vertical',
          backgroundColor: '#1A1F3A',
          paddingAll: '12px',
          contents: [
            { type: 'text', text: `${index + 1}. ${flight.city}`, weight: 'bold', size: 'md', color: '#FFFFFF' },
            { type: 'text', text: `${from} → ${flight.code}`, size: 'xs', color: '#AAB4D4', margin: 'xs' }
          ]
        },
        body: {
          type: 'box',
          layout: 'vertical',
          spacing: 'sm',
          contents: [
            { type: 'text', text: `TWD ${flight.priceTwd.toLocaleString()} 起`, weight: 'bold', size: 'xl', color: '#dc2626' },
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
              color: '#1d4ed8',
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
