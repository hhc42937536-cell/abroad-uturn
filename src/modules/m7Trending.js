import { googleMapsSearchLink, tripLink } from '../services/deepLinks.js';
import { cardAsk, done, quickAsk, textValue } from './shared.js';
import { popularDestinations } from './options.js';

const categories = ['熱門景點', '美食咖啡', '伴手禮', '拍照路線', '雨天備案'];
const trendMap = {
  峴港: {
    熱門景點: ['巴拿山 Sun World', '美溪沙灘', '會安古鎮', '山茶半島靈應寺'],
    美食咖啡: ['Bé Mặn 海鮮', 'Bánh Xèo Bà Dưỡng', 'Cong Caphe', 'Faifo Coffee 會安'],
    伴手禮: ['G7 咖啡', 'Trung Nguyen 咖啡', '腰果', '椰子餅', '韓市場草編包'],
    拍照路線: ['粉紅教堂 -> 龍橋 -> 韓江橋', '美溪沙灘日出', '會安燈籠街夜景'],
    雨天備案: ['Lotte Mart', 'Vincom Plaza', '按摩 SPA', '咖啡店巡禮']
  },
  大阪: {
    熱門景點: ['USJ', '道頓堀', '大阪城', '梅田藍天大廈'],
    美食咖啡: ['一蘭拉麵', '金龍拉麵', '黑門市場', 'HARBS'],
    伴手禮: ['551 蓬萊', 'Pablo 起司塔', 'Calbee+', 'KitKat 限定口味'],
    拍照路線: ['道頓堀固力果', '通天閣新世界', '梅田空中庭園夜景'],
    雨天備案: ['Grand Front Osaka', '阪急百貨', '大阪站地下街', '海遊館']
  },
  澳門: {
    熱門景點: ['大三巴牌坊', '議事亭前地', '威尼斯人', '倫敦人'],
    美食咖啡: ['瑪嘉烈蛋撻', '大利來記豬扒包', '黃枝記', '莫義記'],
    伴手禮: ['鉅記杏仁餅', '咀香園蛋捲', '肉乾', '花生糖'],
    拍照路線: ['大三巴 -> 戀愛巷 -> 瘋堂斜巷', '倫敦人夜景', '永利皇宮纜車'],
    雨天備案: ['威尼斯人購物中心', '巴黎人', '倫敦人', '飯店設施']
  }
};

export const m7 = {
  async start() {
    return cardAsk(
      '現在最夯',
      '選目的地，我會給你現在最適合排進行程的景點、店家、伴手禮和備案。',
      popularDestinations.slice(0, 11),
      1
    );
  },

  async handleStep({ step, state, message }) {
    const value = textValue(message);
    if (step === 1) return quickAsk('想看哪一類？', categories, 2, { destination: value });

    const destination = state.destination;
    const items = trendMap[destination]?.[value] ?? fallbackItems(destination, value);
    return done(trendCard(destination, value, items));
  }
};

function trendCard(destination, category, items) {
  return {
    type: 'flex',
    altText: `${destination} ${category}`,
    contents: {
      type: 'bubble',
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'md',
        contents: [
          { type: 'text', text: `${destination} ${category}`, weight: 'bold', size: 'xl', wrap: true },
          { type: 'text', text: `更新日：${new Date().toISOString().slice(0, 10)}`, size: 'xs', color: '#64748b' },
          ...items.map((item, index) => ({
            type: 'text',
            text: `${index + 1}. ${item}`,
            size: 'sm',
            color: '#374151',
            wrap: true
          }))
        ]
      },
      footer: {
        type: 'box',
        layout: 'vertical',
        spacing: 'sm',
        contents: [
          linkButton('在地圖查看', googleMapsSearchLink(`${destination} ${category}`)),
          linkButton('看旅遊指南', tripLink(destination), '#334155')
        ]
      }
    }
  };
}

function linkButton(label, uri, color = '#2563eb') {
  return { type: 'button', style: 'primary', color, height: 'sm', action: { type: 'uri', label, uri } };
}

function fallbackItems(destination, category) {
  return [
    `${destination} 近期高討論景點`,
    `${destination} 主要商圈與百貨`,
    `${destination} 在地市場與伴手禮店`,
    `${destination} 雨天可改排室內咖啡/展館`
  ].map((item) => `${item}（${category}）`);
}
