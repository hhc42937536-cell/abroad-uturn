import { createItinerary } from '../repositories/itineraryRepository.js';
import { generateTravelPlan } from '../services/openai.js';
import { showLoadingAnimation } from '../services/line.js';
import { searchStarEvents } from '../services/starEvents.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, cardAsk, done, quickAsk, textValue } from './shared.js';

const eventTypes = ['演唱會', '見面會', '音樂節', '頒獎典禮', '快閃活動', '不限'];
const dayOptions = ['2天', '3天', '4天', '5天'];
const confirmOptions = ['安排這場行程', '換其他場次'];
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
      const eventType = normalizeEventType(value);
      const eventSearch = await searchStarEvents(state.artistName, eventType);
      const { options, choices, hasRealEvents } = buildEventOptions(state.artistName, eventType, state.artistCategory, eventSearch);
      return cardAsk(
        hasRealEvents ? '先選場次' : '目前無即時活動資料',
        hasRealEvents
          ? '以下是抓到的場次，先挑一場再安排。'
          : '以下是候選城市（非已確認場次），可先做行程草案。',
        options,
        4,
        { ...state, eventType, eventSearch, slotChoices: choices, hasRealEvents }
      );
    }

    if (step === 4) {
      const picked = parseSlotChoice(value, state.slotChoices);
      if (!picked) {
        const { options, choices } = buildEventOptions(state.artistName, state.eventType, state.artistCategory, state.eventSearch);
        return cardAsk(
          '請重新選場次',
          '剛剛的選項可能過期，請再點一次。',
          options,
          4,
          { ...state, slotChoices: choices }
        );
      }
      return {
        done: false,
        nextStep: 5,
        state: {
          ...state,
          pickedEventLabel: picked.label,
          pickedEventVenue: picked.venue,
          pickedEventDate: picked.date,
          destination: picked.city || inferDestinationByCategory(state.artistCategory)
        },
        messages: [
          eventPreviewCard({
            artistName: state.artistName,
            eventType: state.eventType,
            city: picked.city,
            venue: picked.venue,
            date: picked.date,
            sourceNote: state.eventSearch?.note
          }),
          quickAsk('看完活動內容後，你要？', confirmOptions, 5).messages[0]
        ]
      };
    }

    if (step === 5) {
      if (value === '換其他場次') {
        const { options, choices } = buildEventOptions(state.artistName, state.eventType, state.artistCategory, state.eventSearch);
        return cardAsk(
          '重新選場次',
          '先看活動內容，再選你最想衝的一場。',
          options,
          4,
          { ...state, slotChoices: choices }
        );
      }

      if (value !== '安排這場行程') {
        return quickAsk('請先選擇下一步', confirmOptions, 5, state);
      }

      return quickAsk('這趟追星行程排幾天？', dayOptions, 6, {
        ...state,
        destination: state.destination || inferDestinationByCategory(state.artistCategory)
      });
    }

    if (step === 6) {
      return ask('有沒有指定場館、搶票時間、必去店家或同行狀況？沒有請回「無」。', 7, { ...state, days: value });
    }

    await showLoadingAnimation(lineUserId);
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
    const choices = events.slice(0, 10).map((event) => ({
      city: event.city || '',
      venue: event.venue || `${artistName} ${eventType} 場館`,
      date: event.date || '',
      label: `${event.city || '未定'} ${event.venue || eventType}`
    }));
    return toSlotOptions(choices, eventType, true);
  }

  const fallbackCities = inferLikelyCities(artistCategory);
  const eventTypeLabel = eventType === '不限' ? '全部活動' : eventType;
  const choices = fallbackCities.map((city) => ({
      city,
      venue: `${artistName} ${eventTypeLabel} ${city} 場`,
      date: '日期待官方公告',
      label: `${city} ${eventTypeLabel}`
    }));
  return toSlotOptions(choices, eventTypeLabel, false);
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

function toSlotOptions(choices, eventTypeLabel, hasRealEvents) {
  const options = choices.map((choice, index) => ({
    label: hasRealEvents
      ? `${choice.city || '未定'} ${eventTypeLabel}${index + 1}`
      : `候選 ${choice.city || '未定'} ${index + 1}`,
    value: `slot|${index}`,
    displayText: hasRealEvents
      ? `${choice.city || '未定'} ${eventTypeLabel}${index + 1}`
      : `候選 ${choice.city || '未定'} ${index + 1}`,
    note: hasRealEvents
      ? `${choice.venue}${choice.date ? ` / ${choice.date}` : ''}`
      : `候選城市：${choice.city || '未定'}（尚無已確認場次）`
  }));
  return { options, choices, hasRealEvents };
}

function parseSlotChoice(value, choices = []) {
  const text = String(value || '');
  if (!text.startsWith('slot|')) return null;
  const index = Number(text.split('|')[1]);
  if (!Number.isInteger(index) || index < 0 || index >= choices.length) return null;
  return choices[index];
}

function normalizeEventType(value) {
  return value === '不限' ? '不限' : value;
}

function eventPreviewCard({ artistName, eventType, city, venue, date, sourceNote }) {
  const note = normalizeSourceNote(sourceNote);
  return {
    type: 'flex',
    altText: `${artistName} ${eventType} 活動內容`,
    contents: {
      type: 'bubble',
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'sm',
        contents: [
          { type: 'text', text: '先看活動內容', weight: 'bold', size: 'lg', color: '#111827' },
          keyValue('藝人', artistName || '未填'),
          keyValue('活動', eventType || '未填'),
          keyValue('城市', city || '未定'),
          keyValue('場館', venue || '未定'),
          keyValue('日期', date || '待公告'),
          {
            type: 'text',
            text: note,
            size: 'xs',
            color: '#475569',
            wrap: true
          }
        ]
      }
    }
  };
}

function keyValue(label, value) {
  return {
    type: 'text',
    size: 'sm',
    wrap: true,
    contents: [
      { type: 'span', text: `${label}：`, color: '#2563eb', weight: 'bold' },
      { type: 'span', text: value, color: '#111827' }
    ]
  };
}

function normalizeSourceNote(sourceNote) {
  const text = String(sourceNote || '').trim();
  if (!text) return '目前為推薦候選場次，請再對照官方活動頁與票務平台。';
  if (text.includes('Ticket crawler not configured')) {
    return '活動抓取器尚未接上正式票務來源，目前為候選場次，請再對照官方公告。';
  }
  return text;
}
