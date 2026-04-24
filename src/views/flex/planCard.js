import { agodaLink, bookingLink, skyscannerLink, tripLink } from '../../services/deepLinks.js';

export function planCard(plan, input = {}) {
  const destination = plan.destination ?? input.destination ?? '推薦目的地';
  const days = Array.isArray(plan.days) ? plan.days.slice(0, 5) : [];

  return {
    type: 'flex',
    altText: plan.title ?? '行程建議',
    contents: {
      type: 'bubble',
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'md',
        contents: [
          { type: 'text', text: plan.title ?? '行程建議', weight: 'bold', size: 'xl', wrap: true },
          { type: 'text', text: destination, size: 'md', color: '#2563eb', wrap: true },
          { type: 'text', text: plan.summary ?? '已為你整理出可執行的旅行方向。', wrap: true },
          ...days.map((day) => ({
            type: 'box',
            layout: 'vertical',
            spacing: 'xs',
            contents: [
              { type: 'text', text: `Day ${day.day}`, weight: 'bold' },
              { type: 'text', text: `早：${day.morning ?? '-'}`, wrap: true, size: 'sm' },
              { type: 'text', text: `午：${day.afternoon ?? '-'}`, wrap: true, size: 'sm' },
              { type: 'text', text: `晚：${day.evening ?? '-'}`, wrap: true, size: 'sm' }
            ]
          }))
        ]
      },
      footer: {
        type: 'box',
        layout: 'vertical',
        spacing: 'sm',
        contents: [
          linkButton('查機票', skyscannerLink(input)),
          linkButton('Agoda', agodaLink(destination)),
          linkButton('Booking', bookingLink(destination)),
          linkButton('Trip.com', tripLink(destination))
        ]
      }
    }
  };
}

function linkButton(label, uri) {
  return {
    type: 'button',
    style: 'link',
    height: 'sm',
    action: { type: 'uri', label, uri }
  };
}
