import { googleMapsSearchLink } from '../services/deepLinks.js';
import { cardAsk, done, textValue } from './shared.js';

const cityOptions = [
  '東京',
  '大阪',
  '首爾',
  '曼谷',
  '峴港',
  '河內',
  '澳門',
  '香港',
  '新加坡'
];

const transportProfiles = {
  東京: {
    cards: 'Welcome Suica / PASMO PASSPORT（短期旅客最常用）',
    airport: [
      '成田 NRT -> Skyliner：上野、日暮里（快）',
      '成田 NRT -> NEX：東京、品川、澀谷、新宿（直達）',
      '羽田 HND -> 京急：品川（接 JR 山手線）',
      '羽田 HND -> 東京單軌：濱松町（接 JR 山手線）'
    ],
    lines: [
      'JR 山手線：新宿、澀谷、池袋、上野、東京（第一次去最常用）',
      '地鐵銀座線：淺草、上野、銀座、表參道、澀谷',
      '地鐵丸之內線：新宿、東京、銀座',
      '地鐵半藏門線：澀谷、表參道、押上（晴空塔）'
    ],
    stations: ['新宿站', '東京站', '上野站', '品川站'],
    apps: ['Google Maps', 'Japan Travel by NAVITIME', '乘換案內 (Jorudan)', 'GO Taxi'],
    culture: [
      '電車內講電話會被側目，請改文字訊息。',
      '排隊文化很重，先排再上車。',
      '手扶梯多為左側站立、右側通行（依地區略有差異）。'
    ]
  },
  大阪: {
    cards: 'ICOCA（關西最通用）',
    airport: [
      'KIX -> 南海電鐵：難波（住心齋橋/道頓堀最順）',
      'KIX -> JR 關空快速：天王寺、大阪站',
      'KIX -> 利木津巴士：梅田/難波主要飯店'
    ],
    lines: [
      '御堂筋線：新大阪、梅田、心齋橋、難波、天王寺',
      'JR 大阪環狀線：大阪、天王寺、京橋、西九條',
      '阪急/京阪：大阪往京都常用'
    ],
    stations: ['難波站', '梅田/大阪站', '新大阪站', '天王寺站'],
    apps: ['Google Maps', 'Japan Travel by NAVITIME', 'DiDi', 'GO Taxi'],
    culture: [
      '地鐵轉乘距離可能很長，預留 10-15 分鐘比較穩。',
      '熱門區餐廳排隊常態，晚餐提早到店。',
      'USJ 當天一定提早出門，避免把時間耗在排交通。'
    ]
  },
  首爾: {
    cards: 'T-money（便利商店可買可儲值）',
    airport: [
      'ICN -> AREX 直達：首爾站（快）',
      'ICN -> AREX 普通：弘大、首爾站等',
      'ICN -> 機場巴士：行李多時較輕鬆'
    ],
    lines: [
      '2 號線：弘大、乙支路、江南、蠶室（核心生活圈）',
      '4 號線：明洞、首爾站、東大門',
      '9 號線：汝矣島、江南西側（有急行）'
    ],
    stations: ['弘大入口站', '明洞站', '首爾站', '江南站'],
    apps: ['Naver Map', 'KakaoMap', 'Subway Korea', 'Kakao T'],
    culture: [
      '手扶梯通常右站左走，但以現場標示為準。',
      '公車上下車都要刷卡。',
      '尖峰時段車廂很擠，行李箱請避開尖峰。'
    ]
  },
  曼谷: {
    cards: 'Rabbit Card（BTS）；MRT 可單程或感應支付',
    airport: [
      'BKK -> Airport Rail Link：Phaya Thai（接 BTS）',
      'DMK -> A1/A2 巴士：Mo Chit（接 BTS/MRT）',
      '深夜抵達建議直接 Grab'
    ],
    lines: [
      'BTS Sukhumvit Line：Asok、Siam、Mo Chit',
      'BTS Silom Line：Saphan Taksin、Sala Daeng',
      'MRT Blue Line：Bang Sue、Asok、Silom、Hua Lamphong'
    ],
    stations: ['Asok', 'Siam', 'Sala Daeng', 'Saphan Taksin'],
    apps: ['Google Maps', 'Grab', 'ViaBus'],
    culture: [
      '塞車嚴重，跨區優先 BTS/MRT。',
      '寺廟服裝要注意肩膀與膝蓋遮蔽。',
      '計程車不一定跳表，叫車 App 比較穩。'
    ]
  },
  峴港: {
    cards: '無固定交通卡，市區以 Grab/包車為主',
    airport: [
      'DAD -> 美溪沙灘飯店：Grab 約 15-20 分鐘',
      'DAD -> 市中心韓江區：Grab 約 10-15 分鐘'
    ],
    lines: [
      '市區點對點：Grab 汽車/機車',
      '會安、巴拿山：一日團或包車（最省時間）'
    ],
    stations: ['峴港機場 DAD', '韓市場周邊', '美溪沙灘周邊'],
    apps: ['Grab', 'Google Maps', 'Klook', 'KKday'],
    culture: [
      '機車多，過馬路要穩定速度直行，不要急停急走。',
      '雨季午後易下雨，備輕便雨具。',
      '夜晚海邊風大，回程車先叫好。'
    ]
  },
  河內: {
    cards: '無固定旅客卡，老城區多步行 + Grab',
    airport: [
      'HAN -> 老城區：Grab 約 40-60 分鐘',
      'HAN -> 還劍湖：Grab 或飯店接送'
    ],
    lines: [
      '老城區、還劍湖：步行最有效率',
      '跨區移動：Grab',
      '下龍灣/寧平：一日團接送'
    ],
    stations: ['河內機場 HAN', '還劍湖', '老城區'],
    apps: ['Grab', 'Google Maps', 'Klook', 'KKday'],
    culture: [
      '交通流量大，過馬路請跟著人群節奏走。',
      '熱門店家可能不收卡，備少量現金。',
      'Train Street 開放狀態常變，先查當天資訊。'
    ]
  },
  澳門: {
    cards: '以飯店接駁巴士 + 公車 + 計程車為主',
    airport: [
      'MFM -> 路氹飯店：免費接駁巴士最方便',
      '口岸 -> 半島/路氹：接駁巴士或公車'
    ],
    lines: [
      '半島景點：步行 + 公車',
      '半島 <-> 路氹：飯店接駁巴士'
    ],
    stations: ['澳門機場 MFM', '關閘', '路氹金光大道'],
    apps: ['Google Maps', '澳門巴士資訊 App'],
    culture: [
      '假日熱門景點人多，早上先走大三巴一帶。',
      '飯店接駁通常排隊，預留等車時間。',
      '餐廳尖峰時段候位常見，可先訂位。'
    ]
  },
  香港: {
    cards: '八達通 Octopus（地鐵、公車、便利商店都好用）',
    airport: [
      'HKG -> 機場快線：香港站/九龍站',
      'HKG -> 機場巴士：直達多數市區'
    ],
    lines: [
      '港鐵荃灣線：尖沙咀、旺角、金鐘',
      '港鐵港島線：中環、灣仔、銅鑼灣'
    ],
    stations: ['香港站', '九龍站', '尖沙咀站', '中環站'],
    apps: ['MTR Mobile', 'Google Maps', 'Citymapper'],
    culture: [
      '電扶梯多為右站左行（依現場標示為準）。',
      '上下班尖峰非常擠，避開 8:00-9:30 與 18:00-19:30。',
      '熱門餐廳常要排隊，先拿號碼牌。'
    ]
  },
  新加坡: {
    cards: 'SimplyGo（感應信用卡）或 EZ-Link',
    airport: [
      'SIN -> MRT：樟宜機場線轉市區',
      'SIN -> 計程車/Grab：多人分攤方便'
    ],
    lines: [
      'EW 線：機場轉乘、市中心常用',
      'NS 線：烏節、City Hall、Marina 區',
      'DT 線：Bugis、Little India'
    ],
    stations: ['Changi Airport', 'City Hall', 'Bugis', 'Orchard'],
    apps: ['Citymapper', 'Google Maps', 'Grab'],
    culture: [
      '捷運與公車內禁食禁飲。',
      '法規執行嚴格，公共空間注意標示。',
      '午後常雷陣雨，包包放折傘。'
    ]
  }
};

export const m4 = {
  async start() {
    return cardAsk(
      '當地交通攻略',
      '選城市，我會給你交通卡、機場進市區、線路站點、常用 App 和文化注意事項。',
      cityOptions,
      1
    );
  },

  async handleStep({ message }) {
    const city = textValue(message);
    const guide = transportProfiles[city] ?? fallbackGuide(city);
    return done({
      type: 'flex',
      altText: `${city} 交通攻略`,
      contents: transportCard(city, guide)
    });
  }
};

function transportCard(city, guide) {
  return {
    type: 'bubble',
    size: 'mega',
    body: {
      type: 'box',
      layout: 'vertical',
      spacing: 'md',
      contents: [
        { type: 'text', text: `${city} 交通攻略`, weight: 'bold', size: 'xl', wrap: true, color: '#111827' },
        sectionText('交通卡', guide.cards),
        sectionList('機場進市區', guide.airport),
        sectionList('核心線路', guide.lines),
        sectionList('關鍵站點', guide.stations),
        sectionList('常用 App', guide.apps),
        sectionList('注意事項', guide.culture)
      ]
    },
    footer: {
      type: 'box',
      layout: 'vertical',
      spacing: 'sm',
      contents: [
        linkButton('機場到市區地圖', googleMapsSearchLink(`${city} airport to city`), '#2563eb'),
        linkButton('交通卡購買點', googleMapsSearchLink(`${city} transport card buy`), '#334155'),
        linkButton('車站路線圖', googleMapsSearchLink(`${city} metro line map`), '#0f766e')
      ]
    }
  };
}

function sectionText(title, text) {
  return {
    type: 'text',
    size: 'sm',
    wrap: true,
    contents: [
      { type: 'span', text: `${title}：`, color: '#2563eb', weight: 'bold' },
      { type: 'span', text, color: '#374151' }
    ]
  };
}

function sectionList(title, items) {
  return {
    type: 'box',
    layout: 'vertical',
    spacing: 'xs',
    contents: [
      { type: 'text', text: title, size: 'sm', weight: 'bold', color: '#0f172a' },
      ...items.map((item) => ({
        type: 'text',
        text: `- ${item}`,
        size: 'sm',
        color: '#374151',
        wrap: true
      }))
    ]
  };
}

function linkButton(label, uri, color) {
  return {
    type: 'button',
    style: 'primary',
    color,
    height: 'sm',
    action: { type: 'uri', label, uri }
  };
}

function fallbackGuide(city) {
  return {
    cards: '先查當地儲值交通卡或感應信用卡支付方式。',
    airport: ['優先選機場快線、利木津巴士或官方叫車點。', '深夜抵達先用叫車 App 或飯店接送。'],
    lines: ['先鎖定住宿附近 1-2 條主線，不要一開始就買太多 pass。'],
    stations: [`${city} 主車站`, `${city} 市中心轉乘站`],
    apps: ['Google Maps', '當地叫車 App', '官方地鐵/公車 App'],
    culture: ['尖峰時段預留排隊時間。', '先看車廂禁食/行李規則。', '夜間回程先查末班車時間。']
  };
}
