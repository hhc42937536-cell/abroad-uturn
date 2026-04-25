import { agodaLink, bookingLink, googleMapsSearchLink } from '../services/deepLinks.js';
import { cardAsk, done, quickAsk, textValue } from './shared.js';
import { popularDestinations } from './options.js';

const hotelMap = {
  大阪: [
    ['Hotel Monterey Grasmere Osaka', 'JR 難波直結，難波/心齋橋/道頓堀最順'],
    ['Hotel Vischio Osaka by Granvia', '梅田站旁，去京都、奈良、USJ 都好接'],
    ['Cross Hotel Osaka', '道頓堀旁，吃喝採買最方便']
  ],
  峴港: [
    ['HAIAN Beach Hotel & Spa', '美溪沙灘旁，臨時度假最穩'],
    ['Novotel Danang Premier Han River', '韓江旁，市區與會安動線好接'],
    ['TMS Hotel Da Nang Beach', '海景房型多，走路到沙灘方便']
  ],
  河內: [
    ['La Siesta Classic Ma May', '老城區核心，吃喝景點都能步行'],
    ['Peridot Grand Luxury Boutique Hotel', '還劍湖附近，短天數行程很順'],
    ['The Oriental Jade Hotel', '還劍湖旁，第一次去很穩']
  ],
  澳門: [
    ['Sofitel Macau At Ponte 16', '老城區旁，大三巴和歷史城區很近'],
    ['The Venetian Macao', '路氹金光大道核心，娛樂購物方便'],
    ['Holiday Inn Express Macau City Centre', '市中心平實選擇，交通方便']
  ],
  東京: [
    ['JR Kyushu Hotel Blossom Shinjuku', '新宿站旁，第一次去最省轉車'],
    ['Daiwa Roynet Hotel Ginza Premier', '銀座/東京站動線順'],
    ['Richmond Hotel Premier Asakusa', '淺草上野圈，成田進出方便']
  ],
  首爾: [
    ['L7 Hongdae by LOTTE', '弘大機場快線方便，吃飯採買密度高'],
    ['Nine Tree Premier Hotel Myeongdong 2', '明洞/乙支路動線好'],
    ['LOTTE City Hotel Myeongdong', '市中心交通穩，第一次去好用']
  ]
};

const typeOptions = ['交通最方便', '便宜乾淨', '親子友善', '海景/度假', '購物商圈旁'];

export const m5 = {
  async start() {
    return cardAsk(
      '住宿推薦',
      '選城市，我會直接給可訂的飯店名、適合理由和訂房連結。',
      popularDestinations.slice(0, 11),
      1
    );
  },

  async handleStep({ step, state, message }) {
    const value = textValue(message);
    if (step === 1) return quickAsk('這次住宿最重視什麼？', typeOptions, 2, { city: value });

    const city = state.city;
    const hotels = hotelMap[city] ?? fallbackHotels(city);
    return done(hotelCarousel(city, value, hotels));
  }
};

function hotelCarousel(city, preference, hotels) {
  return {
    type: 'flex',
    altText: `${city} 住宿推薦`,
    contents: {
      type: 'carousel',
      contents: hotels.map(([name, reason]) => ({
        type: 'bubble',
        size: 'micro',
        body: {
          type: 'box',
          layout: 'vertical',
          spacing: 'sm',
          contents: [
            { type: 'text', text: name, weight: 'bold', size: 'md', wrap: true },
            { type: 'text', text: preference, size: 'xs', color: '#7c3aed', weight: 'bold', wrap: true },
            { type: 'text', text: reason, size: 'sm', color: '#374151', wrap: true }
          ]
        },
        footer: {
          type: 'box',
          layout: 'vertical',
          spacing: 'sm',
          contents: [
            linkButton('Booking 訂房', bookingLink(city, name), '#2563eb'),
            linkButton('Agoda 比價', agodaLink(city, name), '#be123c'),
            linkButton('看地圖位置', googleMapsSearchLink(`${city} ${name}`), '#334155')
          ]
        }
      }))
    }
  };
}

function linkButton(label, uri, color) {
  return { type: 'button', style: 'primary', color, height: 'sm', action: { type: 'uri', label, uri } };
}

function fallbackHotels(city) {
  return [
    [`${city} 主要車站旁高評價飯店`, '優先選車站或機場快線沿線，臨時出發最不容易踩雷'],
    [`${city} 市中心商圈飯店`, '吃飯、採買、叫車都方便，適合第一次去'],
    [`${city} 機場交通方便飯店`, '早班機或晚班機比較安全']
  ];
}
