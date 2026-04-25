import { createItinerary } from '../repositories/itineraryRepository.js';
import { generateTravelPlan } from '../services/openai.js';
import { searchStarEvents } from '../services/starEvents.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, cardAsk, done, quickAsk, textValue } from './shared.js';
import { popularDestinations } from './options.js';

const eventTypes = ['演唱會', '見面會', '音樂節', '頒獎典禮', '快閃活動'];
const dayOptions = ['2天', '3天', '4天', '5天'];
const artistCategoryOptions = ['韓國歌手/團體', '韓國演員', '日本偶像', '其他（直接輸入）'];

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
        return ask('請直接輸入藝人或演員名字（例如：IVE / 李敏鎬 / Snow Man）。', 2, state);
      }

      const list = artistsByCategory[value];
      if (list) {
        return cardAsk(
          `${value} - 選藝人`,
          '若名單沒有，可直接輸入名字。',
          list,
          2,
          { ...state, artistCategory: value }
        );
      }

      return quickAsk('是哪一種活動？', eventTypes, 3, { ...state, artistName: value });
    }

    if (step === 2) return quickAsk('是哪一種活動？', eventTypes, 3, { ...state, artistName: value });

    if (step === 3) {
      return cardAsk(
        '活動在哪個城市？',
        '如果還不知道城市，先選最可能的目的地，之後可再調整。',
        popularDestinations.slice(0, 11),
        4,
        { ...state, eventType: value }
      );
    }

    if (step === 4) return quickAsk('這趟追星行程排幾天？', dayOptions, 5, { ...state, destination: value });

    if (step === 5) {
      return ask('有沒有指定場館、搶票時間、必去店家或同行狀況？沒有請回「無」。', 6, { ...state, days: value });
    }

    const eventSearch = await searchStarEvents(state.artistName, state.eventType);
    const input = {
      ...state,
      mustVisit: value === '無' ? `${state.eventType} 場館` : value,
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
