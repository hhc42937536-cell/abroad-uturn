import { createItinerary } from '../repositories/itineraryRepository.js';
import { getUser } from '../repositories/userRepository.js';
import { destinationAirportCode } from '../services/deepLinks.js';
import { quickRouteRecommendations } from '../services/flightSearch.js';
import { generateTravelPlan } from '../services/openai.js';
import { showLoadingAnimation } from '../services/line.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, askWithQuickReplies, cardAsk, done, quickAsk, textValue } from './shared.js';
import { popularDestinations } from './options.js';

const dayOptions = ['2天', '3天', '4天', '5天', '6天', '7天'];
const travelerOptions = ['1人', '2人', '3人', '4人', '5人以上'];

export const m1 = {
  async start() {
    return quickAsk('你有幾天假？', dayOptions, 1);
  },

  async handleStep({ lineUserId, step, state, message }) {
    const value = textValue(message);

    if (step === 1) {
      return askWithQuickReplies(
        '這次幾個人出發？我會用人數估預算，也會避開不適合多人臨時訂的安排。',
        travelerOptions,
        2,
        { days: value }
      );
    }

    if (step === 2) {
      return cardAsk(
        '想去哪裡？',
        '選一個目的地，我會立即排出說走就走行程。',
        [...popularDestinations.slice(0, 11), { label: '其他', value: '其他', note: '輸入你想去的城市', icon: '✍️' }],
        3,
        { ...state, travelerCount: parseTravelerCount(value) }
      );
    }

    if (step === 3 && value === '其他') {
      return ask('請直接輸入目的地城市，例如：札幌、釜山、清邁、河內、峴港、澳門。', 4, state);
    }

    if (step === 3) {
      return askSpecialNeeds({ ...state, destination: value });
    }

    if (step === 4) {
      const prompt = broadDestinationPrompt(value, state.days);
      if (prompt) return ask(prompt, 4, state);
      return askSpecialNeeds({ ...state, destination: value });
    }

    return buildQuickPlan(lineUserId, {
      ...state,
      mustVisit: value === '無' ? '' : value
    });
  }
};

function parseTravelerCount(value) {
  const match = String(value ?? '').match(/\d+/);
  return match ? Number(match[0]) : 5;
}

function askSpecialNeeds(state) {
  return askWithQuickReplies(
    '有必去景點或特殊狀況嗎？可直接輸入（例如：必去築地、帶小孩、要直飛）。沒有就選「無」。',
    ['無', '親子慢步調', '美食優先', '購物優先', '直飛優先', '不要太趕'],
    5,
    state
  );
}

function broadDestinationPrompt(value, days) {
  const text = String(value ?? '').trim();
  const dayText = days ? `${days}` : '這次';
  const prompts = {
    日本: '日本城市很多，請輸入一個城市或地區，例如：東京、大阪、福岡、沖繩、札幌。',
    韓國: '韓國請先指定城市，例如：首爾、釜山、濟州島。',
    越南: '越南請先指定城市，例如：河內、峴港、胡志明市、富國島。',
    泰國: '泰國請先指定城市，例如：曼谷、清邁、普吉島。',
    馬來西亞: '馬來西亞請先指定城市，例如：吉隆坡、檳城、沙巴。',
    菲律賓: '菲律賓請先指定城市，例如：馬尼拉、宿霧、長灘島。',
    印尼: '印尼請先指定城市或島嶼，例如：峇里島、雅加達。',
    中國: '中國城市很多，請輸入一個城市，例如：上海、北京、廣州、深圳、杭州、廈門。',
    美國: `美國範圍太大，${dayText}建議先選一個城市或區域，例如：洛杉磯、紐約、舊金山、西雅圖、夏威夷、關島。`
  };
  return prompts[text] ?? null;
}

async function buildQuickPlan(lineUserId, state) {
  await showLoadingAnimation(lineUserId);
  const user = await getUser(lineUserId);
  const from = user?.departure_airport ?? 'TPE';
  const to = destinationAirportCode(state.destination);
  const flightPicks = to
    ? await quickRouteRecommendations({ origin: from, destination: to })
    : null;

  const input = {
    ...state,
    from,
    to,
    quickDecision: true,
    flightPicks,
    hotelPicks: buildHotelPicks(state.destination)
  };
  const plan = await generateTravelPlan('quick', input);
  await createItinerary(lineUserId, {
    module: 'M1',
    destination: plan.destination,
    travelerCount: state.travelerCount ?? user?.default_traveler_count ?? 1,
    content: { ...plan, flightPicks, hotelPicks: input.hotelPicks }
  }).catch((error) => {
    console.error('Failed to save quick trip itinerary', error);
  });
  return done(planCard(plan, input));
}

function buildHotelPicks(destination) {
  const normalized = String(destination ?? '').trim();
  const picked = hotelRecommendations[normalized] ?? fallbackHotelRecommendations(normalized);

  return {
    best: {
      label: '推薦直接訂',
      ...picked.best
    },
    backup: {
      label: '備案',
      ...picked.backup
    }
  };
}

const hotelRecommendations = {
  東京: hotelPair(
    'JR Kyushu Hotel Blossom Shinjuku',
    '新宿站旁，臨時出發最省轉車時間',
    'Daiwa Roynet Hotel Ginza Premier',
    '銀座/東京站動線順，採買和機場交通方便'
  ),
  大阪: hotelPair(
    'Hotel Monterey Grasmere Osaka',
    'JR 難波直結，難波/心齋橋/道頓堀最順',
    'Hotel Vischio Osaka by Granvia',
    '梅田站旁，去京都、奈良、USJ 都好接'
  ),
  首爾: hotelPair(
    'L7 Hongdae by LOTTE',
    '弘大機場快線方便，吃飯採買密度高',
    'Nine Tree Premier Hotel Myeongdong 2',
    '明洞/乙支路動線好，第一次去很穩'
  ),
  曼谷: hotelPair(
    'Grande Centre Point Terminal 21',
    'Asok 站直結，BTS/MRT 雙線超方便',
    'Mercure Bangkok Siam',
    'Siam 商圈旁，百貨和美食最省時間'
  ),
  香港: hotelPair(
    'The Royal Pacific Hotel & Towers',
    '尖沙咀交通與購物方便，機場巴士好接',
    'Eaton HK',
    '佐敦站旁，去旺角、尖沙咀、中環都順'
  ),
  新加坡: hotelPair(
    'Carlton Hotel Singapore',
    'City Hall/Bras Basah 中間，景點和 MRT 都方便',
    'lyf Funan Singapore',
    'Funan 商場內，短天數機能很強'
  ),
  福岡: hotelPair(
    'JR Kyushu Hotel Blossom Hakata Central',
    '博多站旁，機場、市區、太宰府都好接',
    'Richmond Hotel Tenjin Nishidori',
    '天神商圈中心，逛街採買最方便'
  ),
  沖繩: hotelPair(
    'Hotel Gracery Naha',
    '國際通旁，不開車也能吃買方便',
    'Mercure Hotel Okinawa Naha',
    '壺川站旁，單軌和取車動線都穩'
  ),
  吉隆坡: hotelPair(
    'Pavilion Hotel Kuala Lumpur Managed by Banyan Tree',
    'Bukit Bintang 商圈直結，說走就走最省心',
    'Traders Hotel Kuala Lumpur',
    'KLCC 景點旁，雙子星和市中心動線佳'
  ),
  胡志明市: hotelPair(
    'Fusion Original Saigon Centre',
    '第一郡 Saigon Centre 內，吃買叫車都方便',
    'Silverland Yen Hotel',
    '濱城市場附近，景點可步行串接'
  ),
  馬尼拉: hotelPair(
    'Seda Bonifacio Global City',
    'BGC 安全好逛，餐廳和商場集中',
    'Holiday Inn & Suites Makati',
    'Makati 商場直結，短天數移動省事'
  ),
  峇里島: hotelPair(
    'Courtyard by Marriott Bali Seminyak Resort',
    'Seminyak 海灘和餐廳方便，第一次去穩',
    'Alaya Resort Ubud',
    '烏布核心區，市場、餐廳和文化景點好接'
  ),
  河內: hotelPair(
    'La Siesta Classic Ma May',
    '老城區核心，吃喝景點都能步行',
    'Peridot Grand Luxury Boutique Hotel',
    '還劍湖附近，短天數行程很順'
  ),
  峴港: hotelPair(
    'HAIAN Beach Hotel & Spa',
    '美溪沙灘旁，海邊度假和市區都好接',
    'Novotel Danang Premier Han River',
    '韓江旁，去市區、會安、巴拿山動線穩'
  ),
  澳門: hotelPair(
    'Sofitel Macau At Ponte 16',
    '老城區旁，大三巴和歷史城區很近',
    'The Venetian Macao',
    '路氹金光大道核心，飯店娛樂和接駁方便'
  )
};

function hotelPair(bestTitle, bestReason, backupTitle, backupReason) {
  return {
    best: { title: bestTitle, reason: bestReason, keyword: bestTitle },
    backup: { title: backupTitle, reason: backupReason, keyword: backupTitle }
  };
}

function fallbackHotelRecommendations(destination) {
  const city = destination || '目的地';
  return hotelPair(
    `${city} 主要車站旁飯店`,
    '優先選主車站或機場快線直達區，臨時出發最不容易踩雷',
    `${city} 市中心高評價飯店`,
    '備案選市中心高評價住宿，保留交通和吃飯彈性'
  );
}
