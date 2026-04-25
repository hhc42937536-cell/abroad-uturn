import { createItinerary } from '../repositories/itineraryRepository.js';
import { generateTravelPlan } from '../services/openai.js';
import { searchStarEvents } from '../services/starEvents.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, cardAsk, done, quickAsk, textValue } from './shared.js';

const eventTypes = ['演唱會', '見面會', '音樂節', '頒獎典禮', '快閃活動'];
const dayOptions = ['2天', '3天', '4天', '5天'];
const artistCategoryOptions = ['韓國歌手/團體', '韓國演員', '日本偶像', '其他（直接輸入）'];
const searchArtistValue = '__SEARCH_ARTIST__';
const searchArtistOption = {
  label: '🔎 搜尋未列出',
  value: searchArtistValue,
  displayText: '搜尋未列出'
};

const artistsByCategory = {
  '韓國歌手/團體': [
    'BLACKPINK',
    'BTS',
    'TWICE',
    'SEVENTEEN',
    'Stray Kids',
    'ENHYPEN',
    'aespa',
    'IVE',
    'LE SSERAFIM',
    'NewJeans',
    'IU'
  ],
  '韓國演員': [
    '李敏鎬',
    '朴敘俊',
    '玄彬',
    '宋仲基',
    '金秀賢',
    '孔劉',
    '丁海寅',
    '韓韶禧',
    '朴敏英',
    '金智媛',
    '秀智'
  ],
  '日本偶像': [
    'Snow Man',
    'SixTONES',
    'なにわ男子',
    'JO1',
    'INI',
    '乃木坂46',
    '櫻坂46',
    '日向坂46',
    'King & Prince',
    'Travis Japan',
    'WEST.'
  ]
};

export const m8 = {
  async start() {
    return cardAsk(
      '追星行程規劃',
      '先選類型（韓國歌手/韓國演員/日本偶像），也可直接輸入藝人名字。',
      artistCategoryOptions,
      1
    );
  },

  async handleStep({ lineUserId, step, state, message }) {
    const value = textValue(message);

    if (step === 1) {
      if (value === '其他（直接輸入）') {
        return ask('請直接輸入藝人或演員名字（例如：IVE / 李敏鎬 / Snow Man）。', 2, { ...state, awaitingArtistInput: true });
      }

      const list = artistsByCategory[value];
      if (list) {
        return cardAsk(
          `${value} - 選藝人`,
          '若名單沒有，請點「搜尋藝人/演員（未列出）」。',
          [...list, searchArtistOption],
          2,
          { ...state, artistCategory: value }
        );
      }

      return quickAsk('是哪一種活動？', eventTypes, 3, { ...state, artistName: value });
    }

    if (step === 2) {
      if (value === searchArtistValue || state.awaitingArtistInput) {
        if (state.awaitingArtistInput) {
          return quickAsk('是哪一種活動？', eventTypes, 3, { ...state, artistName: value, awaitingArtistInput: false });
        }
        return ask('請輸入要搜尋的藝人或演員名字（中/英都可）。', 2, { ...state, awaitingArtistInput: true });
      }
      return quickAsk('是哪一種活動？', eventTypes, 3, { ...state, artistName: value, awaitingArtistInput: false });
    }

    if (step === 3) {
      const eventSearch = await searchStarEvents(state.artistName, value);
      const options = buildEventOptions(state.artistName, value, state.artistCategory, eventSearch);
      return cardAsk(
        '先選場次',
        '依活動類型先挑一場，不再先問城市。',
        options,
        4,
        { ...state, eventType: value, eventSearch }
      );
    }

    if (step === 4) {
      const picked = parseEventValue(value);
      return quickAsk('這趟追星行程排幾天？', dayOptions, 5, {
        ...state,
        pickedEventLabel: picked.label,
        pickedEventVenue: picked.venue,
        pickedEventDate: picked.date,
        destination: picked.city || inferDestinationByCategory(state.artistCategory)
      });
    }

    if (step === 5) {
      return ask('有沒有指定場館、搶票時間、必去店家或同行狀況？沒有請回「無」。', 6, { ...state, days: value });
    }

    const eventSearch = state.eventSearch ?? await searchStarEvents(state.artistName, state.eventType);
    const input = {
      ...state,
      mustVisit: value === '無'
        ? `${state.pickedEventVenue || state.eventType} 場館`
        : `${state.pickedEventVenue || state.eventType} / ${value}`,
      eventSearch
    };
    const plan = await generateTravelPlan('star_trip', input);
    await createItinerary(lineUserId, {
      module: 'M8',
      destination: plan.destination ?? input.destination,
      content: { ...plan, eventSearch }
    }).catch((error) => {
      console.error('Failed to save star trip itinerary', error);
    });
    return done(planCard(plan, input));
  }
};

function buildEventOptions(artistName, eventType, artistCategory, eventSearch) {
  const events = Array.isArray(eventSearch?.events) ? eventSearch.events : [];
  if (events.length) {
    return events.slice(0, 10).map((event, index) => ({
      label: `${event.city || '未定'} ${event.date || ''}`.trim(),
      value: stringifyEventValue({
        city: event.city || '',
        venue: event.venue || `${artistName} ${eventType} 場館`,
        date: event.date || '',
        label: `${event.city || '未定'} ${event.venue || eventType}`
      }),
      note: `${event.venue || eventType}${event.date ? ` / ${event.date}` : ''}`
    }));
  }

  const fallbackCities = inferLikelyCities(artistCategory);
  return fallbackCities.map((city, index) => ({
    label: `${city} ${eventType}${index + 1}`,
    value: stringifyEventValue({
      city,
      venue: `${artistName} ${eventType} ${city} 場`,
      date: '日期待官方公告',
      label: `${city} ${eventType}`
    }),
    note: `推薦先鎖定 ${city} 場次`
  }));
}

function inferLikelyCities(artistCategory) {
  if (artistCategory === '韓國歌手/團體' || artistCategory === '韓國演員') {
    return ['首爾', '釜山', '東京'];
  }
  if (artistCategory === '日本偶像') {
    return ['東京', '大阪', '福岡'];
  }
  return ['東京', '首爾', '大阪'];
}

function inferDestinationByCategory(artistCategory) {
  if (artistCategory === '韓國歌手/團體' || artistCategory === '韓國演員') return '首爾';
  if (artistCategory === '日本偶像') return '東京';
  return '東京';
}

function stringifyEventValue(data) {
  return `event|${data.city || ''}|${data.venue || ''}|${data.date || ''}|${data.label || ''}`;
}

function parseEventValue(value) {
  const text = String(value || '');
  if (!text.startsWith('event|')) {
    return { city: '', venue: text, date: '', label: text };
  }
  const [, city, venue, date, label] = text.split('|');
  return { city, venue, date, label };
}
