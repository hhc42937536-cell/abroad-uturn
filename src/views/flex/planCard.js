import { agodaLink, bookingLink, destinationAirportCode, googleMapsSearchLink, skyscannerLink, tripLink } from '../../services/deepLinks.js';

export function planCard(plan, input = {}) {
  const destination = plan.destination ?? input.destination ?? '目的地';
  const days = Array.isArray(plan.days) ? plan.days.slice(0, 7) : [];
  const flightInput = {
    ...input,
    destination,
    to: input.to || destinationAirportCode(destination)
  };

  return {
    type: 'flex',
    altText: plan.title ?? '旅程規劃',
    contents: {
      type: 'bubble',
      size: 'mega',
      header: {
        type: 'box',
        layout: 'vertical',
        backgroundColor: '#1A1F3A',
        paddingAll: '20px',
        contents: [
          { type: 'text', text: plan.title ?? '旅程規劃', weight: 'bold', size: 'lg', color: '#FFFFFF', wrap: true },
          { type: 'text', text: destination, size: 'md', color: '#93C5FD', weight: 'bold', wrap: true, margin: 'xs' },
          {
            type: 'text',
            text: plan.summary ?? '已整理一份可直接出發的行程草案。',
            size: 'xs',
            color: '#AAB4D4',
            wrap: true,
            margin: 'sm'
          }
        ]
      },
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'md',
        contents: [
          ...(input.quickDecision ? quickDecisionSummary(input, plan) : []),
          sectionTitle('每日安排'),
          ...days.map((day, index) => dayBlock(day, index))
        ]
      },
      footer: {
        type: 'box',
        layout: 'vertical',
        spacing: 'sm',
        contents: input.quickDecision
          ? quickDecisionButtons(destination, flightInput)
          : standardButtons(destination, flightInput)
      }
    }
  };
}

function quickDecisionSummary(input, plan) {
  const destination = plan.destination ?? input.destination;
  return [
    flightDecisionCard(input.flightPicks, input),
    hotelDecisionCard(input.hotelPicks, destination),
    budgetCard(plan.budget)
  ].filter(Boolean);
}

function flightDecisionCard(picks = {}, input = {}) {
  const cheapest = picks.cheapest;
  const fastest = picks.fastest;
  const samePick = cheapest && fastest
    && cheapest.route === fastest.route
    && cheapest.departDate === fastest.departDate
    && cheapest.priceText === fastest.priceText;

  return infoCard('機票我先幫你選', samePick
    ? [
        tagText('最便宜 / 最快直飛同一班', '#16a34a'),
        routeText(cheapest),
        highlightRow([
          ['價格', cheapest.priceText, '#dc2626'],
          ['時間', `${cheapest.duration || '-'} ${cheapest.stops || ''}`.trim(), '#2563eb']
        ]),
        smallText(`日期：${cheapest.departDate || '近7天內'}`),
        inlineLinkButton('點進去買這班', flightLink(input, cheapest), '#1d4ed8')
      ]
    : [
        tagText('近7天最便宜', '#16a34a'),
        routeText(cheapest),
        highlightRow([['價格', cheapest?.priceText ?? '查詢中', '#dc2626'], ['日期', cheapest?.departDate ?? '近7天內', '#2563eb']]),
        tagText('最快/直飛建議', '#0f766e'),
        routeText(fastest),
        highlightRow([['時間', `${fastest?.duration || '-'} ${fastest?.stops || ''}`.trim(), '#2563eb'], ['價格', fastest?.priceText ?? '查詢中', '#dc2626']]),
        buttonRow([
          inlineLinkButton('買最便宜', flightLink(input, cheapest), '#1d4ed8'),
          inlineLinkButton('查最快', flightLink(input, fastest), '#0f766e')
        ])
      ]);
}

function hotelDecisionCard(hotels = {}, destination = '') {
  const best = hotels.best;
  const backup = hotels.backup;
  return infoCard('住宿我先幫你選', [
    tagText(best?.label ?? '推薦直接訂', '#7c3aed'),
    strongText(best?.title ?? `${destination} 市中心/主要車站旁邊`),
    ...(best?.reason ? [smallText(best.reason)] : []),
    buttonRow([
      inlineLinkButton('Booking 訂這間', bookingLink(destination, best?.keyword ?? best?.title), '#2563eb'),
      inlineLinkButton('Agoda 看價格', agodaLink(destination, best?.keyword ?? best?.title), '#be123c')
    ]),
    tagText('備案', '#ea580c'),
    strongText(backup?.title ?? `${destination} 機場快線/直達巴士沿線`),
    ...(backup?.reason ? [smallText(backup.reason)] : []),
    inlineLinkButton('訂備案住宿', bookingLink(destination, backup?.keyword ?? backup?.title), '#7c3aed')
  ]);
}

function budgetCard(budget) {
  if (!budget) return null;
  return infoCard('預算先抓這樣', [
    highlightSingle(budget.title ?? '總預算', budget.totalText, '#dc2626'),
    ...budget.lines.map((line) => smallText(line)),
    smallText(budget.note)
  ]);
}

const dayPalette = [
  { bg: '#EEF2FF', border: '#C7D2FE', label: '#283593' },
  { bg: '#FFF3EE', border: '#FED7AA', label: '#BF360C' },
  { bg: '#E8F5E9', border: '#BBF7D0', label: '#166534' },
  { bg: '#E1F5FE', border: '#BAE6FD', label: '#075985' },
  { bg: '#F3E5F5', border: '#E9D5FF', label: '#6B21A8' },
  { bg: '#FFFBEA', border: '#FEF08A', label: '#854D0E' },
  { bg: '#E0F2F1', border: '#99F6E4', label: '#115E59' }
];

function dayBlock(day, index = 0) {
  const color = dayPalette[index % dayPalette.length];
  return {
    type: 'box',
    layout: 'vertical',
    spacing: 'xs',
    paddingAll: '10px',
    backgroundColor: color.bg,
    borderColor: color.border,
    borderWidth: '1px',
    cornerRadius: 'md',
    contents: [
      { type: 'text', text: `Day ${day.day}`, weight: 'bold', size: 'sm', color: color.label },
      timeText('上午', day.morning),
      timeText('下午', day.afternoon),
      timeText('晚上', day.evening)
    ]
  };
}

function infoCard(title, contents) {
  return {
    type: 'box',
    layout: 'vertical',
    spacing: 'xs',
    paddingAll: '10px',
    backgroundColor: '#f8fafc',
    cornerRadius: 'md',
    contents: [
      { type: 'text', text: title, weight: 'bold', size: 'sm', color: '#0f172a' },
      ...contents.filter(Boolean)
    ]
  };
}

function sectionTitle(text) {
  return { type: 'text', text, weight: 'bold', size: 'sm', color: '#0f172a', margin: 'sm' };
}

function tagText(text, color) {
  return { type: 'text', text, size: 'xs', color, weight: 'bold', wrap: true };
}

function strongText(text) {
  return { type: 'text', text, size: 'sm', color: '#111827', weight: 'bold', wrap: true };
}

function smallText(text) {
  return { type: 'text', text, size: 'xs', color: '#475569', wrap: true };
}

function routeText(item) {
  if (!item) return smallText('暫時沒有即時資料，請用下方按鈕自行查詢。');
  return { type: 'text', text: item.route, size: 'md', color: '#111827', weight: 'bold', wrap: true };
}

function highlightSingle(label, value, color) {
  return {
    type: 'text',
    size: 'sm',
    wrap: true,
    contents: [
      { type: 'span', text: `${label}：`, color: '#475569' },
      { type: 'span', text: value, color, weight: 'bold' }
    ]
  };
}

function highlightRow(items) {
  return {
    type: 'box',
    layout: 'horizontal',
    spacing: 'sm',
    contents: items.map(([label, value, color]) => ({
      type: 'box',
      layout: 'vertical',
      flex: 1,
      paddingAll: '6px',
      backgroundColor: '#ffffff',
      cornerRadius: 'sm',
      contents: [
        { type: 'text', text: label, size: 'xxs', color: '#64748b' },
        { type: 'text', text: value, size: 'sm', color, weight: 'bold', wrap: true }
      ]
    }))
  };
}

function timeText(label, value) {
  return {
    type: 'text',
    size: 'sm',
    color: '#374151',
    wrap: true,
    contents: [
      { type: 'span', text: `${label}：`, color: '#2563eb', weight: 'bold' },
      { type: 'span', text: value ?? '-' }
    ]
  };
}

function quickDecisionButtons(destination, flightInput) {
  const bestHotel = flightInput.hotelPicks?.best;
  return [
    buttonRow([
      linkButton('直接訂機票', skyscannerLink(flightInput), '#1d4ed8'),
      linkButton('訂推薦飯店', bookingLink(destination, bestHotel?.keyword ?? bestHotel?.title), '#7c3aed')
    ]),
    buttonRow([
      linkButton('住宿地圖', googleMapsSearchLink(`${destination} ${bestHotel?.title ?? '市中心 主要車站 飯店'}`), '#2563eb'),
      linkButton('景點地圖', googleMapsSearchLink(`${destination} 景點`), '#334155')
    ]),
    exportPlanButton()
  ];
}

function flightLink(input, pick) {
  return skyscannerLink({
    from: input.from,
    to: input.to,
    destination: input.destination,
    departDate: pick?.departDate
  });
}

function standardButtons(destination, flightInput) {
  return [
    buttonRow([
      linkButton('查機票', skyscannerLink(flightInput), '#1d4ed8'),
      linkButton('Agoda', agodaLink(destination), '#be123c')
    ]),
    buttonRow([
      linkButton('Booking', bookingLink(destination), '#2563eb'),
      linkButton('Trip.com', tripLink(destination), '#334155')
    ]),
    exportPlanButton()
  ];
}

function buttonRow(contents) {
  return { type: 'box', layout: 'horizontal', spacing: 'sm', contents };
}

function linkButton(label, uri, color = '#2563eb') {
  return {
    type: 'button',
    style: 'primary',
    color,
    height: 'sm',
    flex: 1,
    action: { type: 'uri', label, uri }
  };
}

function inlineLinkButton(label, uri, color = '#2563eb') {
  return {
    type: 'button',
    style: 'primary',
    color,
    height: 'sm',
    flex: 1,
    margin: 'xs',
    action: { type: 'uri', label, uri }
  };
}

function exportPlanButton() {
  return {
    type: 'button',
    style: 'secondary',
    height: 'sm',
    margin: 'sm',
    action: {
      type: 'postback',
      label: '📋 產出計畫書',
      data: 'action=export_plan',
      displayText: '📋 產出計畫書'
    }
  };
}
