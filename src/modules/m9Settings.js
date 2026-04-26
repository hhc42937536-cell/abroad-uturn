import { updateUserSettings } from '../repositories/userRepository.js';
import { mainMenuFlex } from '../views/flex/mainMenu.js';
import { cardAsk, done, textValue } from './shared.js';

const menuOptions = [
  { label: '設定出發地', value: 'set_airport', icon: '✈️', note: '查機票、估預算時自動套用' },
  { label: '說明', value: 'about', icon: '📖', note: '功能介紹與使用方式' }
];

const airportOptions = [
  { label: '桃園 TPE', value: 'TPE', city: '台北', note: '國際線最多，大多數出國首選。' },
  { label: '松山 TSA', value: 'TSA', city: '台北', note: '市區直達，東京首爾上海最適。' },
  { label: '高雄 KHH', value: 'KHH', city: '高雄', note: '南部出發首選，日韓東南亞都方便。' },
  { label: '台中 RMQ', value: 'RMQ', city: '台中', note: '中部旅客省去北上時間。' },
  { label: '台南 TNN', value: 'TNN', city: '台南', note: '台南旅客專屬，進出最省時。' }
];

export const m9 = {
  async start() {
    return cardAsk('設定', '選擇要做什麼。', menuOptions, 1);
  },

  async handleStep({ lineUserId, step, message }) {
    const value = textValue(message);

    if (step === 1) {
      if (value === 'about') {
        return done([aboutFlex(), mainMenuFlex()]);
      }
      return cardAsk(
        '選擇出發機場',
        '設定後查機票和估預算會自動套用。',
        airportOptions.map((a) => ({
          label: a.label,
          value: `${a.city}|${a.value}`,
          displayText: `設定 ${a.label}`,
          note: a.note
        })),
        2
      );
    }

    const [departureCity, departureAirport] = parseAirport(value);
    const saved = await updateUserSettings(lineUserId, { departureCity, departureAirport });
    return done([confirmationFlex(saved), mainMenuFlex()]);
  }
};

function confirmationFlex(saved) {
  return {
    type: 'flex',
    altText: '出發地已設定',
    contents: {
      type: 'bubble',
      header: {
        type: 'box',
        layout: 'vertical',
        backgroundColor: '#1A1F3A',
        paddingAll: '16px',
        contents: [
          { type: 'text', text: '✈️ 出發地已設定', weight: 'bold', size: 'lg', color: '#FFFFFF' },
          { type: 'text', text: '查機票、排行程都會直接套用。', size: 'xs', color: '#AAB4D4', margin: 'xs' }
        ]
      },
      body: {
        type: 'box',
        layout: 'vertical',
        paddingAll: '16px',
        contents: [
          {
            type: 'text',
            text: `${saved.departure_city}（${saved.departure_airport}）`,
            weight: 'bold',
            size: 'xl',
            color: '#1A1F3A',
            align: 'center'
          }
        ]
      }
    }
  };
}

function aboutFlex() {
  const modules = [
    ['🚀', 'M1 說走就走', '2–7 天快速行程，AI 直接排好每日安排'],
    ['✨', 'M2 完整出國規劃', '8 步詳細計畫，含預算風格與住宿偏好'],
    ['✈️', 'M3 探索最便宜', '從你的機場出發，找近期最低價目的地'],
    ['🚇', 'M4 當地交通攻略', '交通卡、機場進市區、常用 App 與提醒'],
    ['🏨', 'M5 住宿推薦', '各城市直接推薦可訂飯店與訂房連結'],
    ['📋', 'M6 行前必知', '簽證、匯率、插座、打包清單'],
    ['🔥', 'M7 現在最夯', '最新熱門景點、必買清單、爆款玩法'],
    ['⭐', 'M8 追星行程規劃', '依演唱會場次安排含住宿交通的追星行程'],
    ['⚙️', 'M9 設定', '設定出發機場，查看說明']
  ];

  return {
    type: 'flex',
    altText: '出國優轉 功能說明',
    contents: {
      type: 'bubble',
      size: 'mega',
      header: {
        type: 'box',
        layout: 'vertical',
        backgroundColor: '#1A1F3A',
        paddingAll: '16px',
        contents: [
          { type: 'text', text: '📖 出國優轉 功能說明', weight: 'bold', size: 'lg', color: '#FFFFFF' },
          { type: 'text', text: '輸入「選單」隨時回到主選單', size: 'xs', color: '#AAB4D4', margin: 'xs' }
        ]
      },
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'sm',
        paddingAll: '14px',
        contents: modules.map(([icon, name, desc]) => ({
          type: 'box',
          layout: 'vertical',
          spacing: 'xs',
          contents: [
            {
              type: 'box',
              layout: 'horizontal',
              spacing: 'sm',
              contents: [
                { type: 'text', text: icon, size: 'sm', flex: 0 },
                { type: 'text', text: name, size: 'sm', weight: 'bold', color: '#1A1F3A', flex: 1 }
              ]
            },
            { type: 'text', text: desc, size: 'xs', color: '#6B7280', wrap: true, margin: 'xs' }
          ]
        }))
      }
    }
  };
}

function parseAirport(value) {
  if (value.includes('|')) return value.split('|');
  const code = value.toUpperCase();
  const airport = airportOptions.find((a) => a.value === code) ?? airportOptions[0];
  return [airport.city, airport.value];
}
