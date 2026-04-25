import { googleMapsDirectionsLink, googleMapsSearchLink, googleSearchLink } from '../services/deepLinks.js';
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

const cityAliases = {
  東京: ['東京', '日本', 'tokyo', 'jp', 'japan'],
  大阪: ['大阪', 'osaka', '關西', 'kansai'],
  首爾: ['首爾', '韓國', 'seoul', 'korea', 'kr', '서울'],
  曼谷: ['曼谷', '泰國', 'bangkok', 'thailand', 'th'],
  峴港: ['峴港', 'danang', 'da nang', '越南中部'],
  河內: ['河內', 'hanoi', '越南北部'],
  澳門: ['澳門', 'macau', 'macao'],
  香港: ['香港', 'hong kong', 'hk'],
  新加坡: ['新加坡', 'singapore', 'sg']
};

const transportProfiles = {
  東京: {
    cards: 'Welcome Suica（短期旅客常用）；長住可評估一般 Suica/PASMO',
    cardNotes: [
      'Welcome Suica 短期卡有效期 28 天，逾期不能再使用。',
      'Welcome Suica 無押金；一般情況餘額不退（含到期後剩餘金額）。',
      '僅卡片故障且符合 JR 規範時，才可走故障退款流程，不是一般退卡機制。',
      'Welcome Suica 遺失不可補發，請不要一次儲值過多。',
      'Welcome Suica 不能跨不同區域連續搭乘（例如東京直刷到仙台不行）。',
      '儲值以現金為主，建議把「回程最後一天」預估後再加值，避免殘值。',
      '卡面 GOOD THRU 不是你的 28 天效期，效期以購卡憑證（Reference Paper）為準。',
      'PASMO PASSPORT 已於 2024-10 停止後續處理，旅客建議以 Welcome Suica 或一般 IC 卡替代。'
    ],
    airport: [
      '成田 NRT -> Skyliner：上野、日暮里',
      '成田 NRT -> NEX：東京、品川、澀谷、新宿',
      '羽田 HND -> 京急：品川（轉 JR 山手線）',
      '羽田 HND -> 東京單軌：濱松町（轉 JR 山手線）'
    ],
    lines: [
      'JR 山手線：新宿、澀谷、池袋、上野、東京',
      '銀座線：淺草、上野、銀座、表參道、澀谷',
      '丸之內線：新宿、東京、銀座',
      '半藏門線：澀谷、表參道、押上（晴空塔）'
    ],
    stations: [
      '新宿站：山手線與私鐵轉乘核心，往近郊與市區都快。',
      '東京站：新幹線與多條 JR 幹線樞紐，跨城市移動主力。',
      '上野站：往成田與東北方向常用節點，阿美橫町也近。',
      '品川站：羽田進市區常見轉乘點，新幹線也可直上。'
    ],
    apps: [
      'Google Maps：查即時路線、月台與步行時間。',
      'Japan Travel by NAVITIME：跨區鐵道規劃與票券建議。',
      '乘換案內 (Jorudan)：看首末班與轉乘時間細節。',
      'GO Taxi：深夜或行李多時快速叫車。'
    ],
    culture: [
      '車廂內避免講電話，請改文字訊息。',
      '月台排隊文化很重，先排再上車。',
      '尖峰車廂很擠，行李箱儘量避開 7:30-9:30。'
    ],
    map: { airportOrigin: '成田機場', cityDestination: '東京車站' }
  },
  大阪: {
    cards: 'ICOCA（關西最通用）',
    cardNotes: [
      'ICOCA 可在關西多數鐵道與便利商店使用，離境前可到指定窗口處理退卡。',
      '若是短期行程，先用 ICOCA + 單次特急券，通常比亂買多張 pass 省。',
      '跨公司列車（JR/私鐵/地鐵）轉乘時，先看閘門與票券適用範圍。'
    ],
    airport: [
      'KIX -> 南海電鐵：難波',
      'KIX -> JR 關空快速：天王寺、大阪站',
      'KIX -> 利木津巴士：梅田、難波主要飯店'
    ],
    lines: [
      '御堂筋線：新大阪、梅田、心齋橋、難波、天王寺',
      'JR 大阪環狀線：大阪、天王寺、京橋、西九條',
      '阪急/京阪：大阪往京都常用'
    ],
    stations: [
      '難波站：南海與地鐵核心，關西機場進城常用。',
      '梅田/大阪站：北區商圈中心，JR/阪急/阪神轉乘密集。',
      '新大阪站：新幹線進出大阪主站，跨城必經。',
      '天王寺站：南區大站，往奈良與市區東南側方便。'
    ],
    apps: [
      'Google Maps：查換乘動線與步行距離。',
      'Japan Travel by NAVITIME：JR/私鐵混搭路線規劃。',
      'DiDi：市區短程與深夜叫車。',
      'GO Taxi：尖峰備援叫車。'
    ],
    culture: [
      '地鐵轉乘走路距離可能很長，預留 10-15 分鐘。',
      '熱門餐廳排隊常態，晚餐建議提早到店。',
      'USJ 當天一定早出門，避免把時間卡在交通。'
    ],
    map: { airportOrigin: '關西國際機場', cityDestination: '難波站' }
  },
  首爾: {
    cards: 'T-money（便利商店可買可儲值）',
    cardNotes: [
      'T-money 幾乎是首爾移動標配，地鐵公車都通用。',
      '公車上下車都要刷，漏刷會影響轉乘優惠。',
      '機場快線 AREX 與一般地鐵票價不同，轉乘前先確認車種。'
    ],
    airport: [
      'ICN -> AREX 直達：首爾站（最快）',
      'ICN -> AREX 普通：弘大、首爾站等',
      'ICN -> 機場巴士：行李多時較輕鬆'
    ],
    lines: [
      '2 號線：弘大、乙支路、江南、蠶室',
      '4 號線：明洞、首爾站、東大門',
      '9 號線：汝矣島、江南西側（有急行）'
    ],
    stations: [
      '弘大入口站：機場線與 2 號線交會，旅客住宿密集。',
      '明洞站：購物與市中心景點最常用下車點。',
      '首爾站：AREX、KTX、地鐵匯集，跨城與機場主樞紐。',
      '江南站：商務與購物區核心，2 號線高頻站。'
    ],
    apps: [
      'Naver Map：韓國在地導航最準，地址搜尋成功率高。',
      'KakaoMap：路線備援與周邊店家評價查看。',
      'Subway Korea：離線地鐵圖與站間時間。',
      'Kakao T：計程車叫車與預估車資。'
    ],
    culture: [
      '公車上下車都要刷卡。',
      '尖峰時段車廂很擠，行李箱請避開通勤時段。',
      '部分店家對一人用餐有限制，先看店規。'
    ],
    map: { airportOrigin: '仁川國際機場', cityDestination: '首爾站' }
  },
  曼谷: {
    cards: 'Rabbit Card（BTS）；MRT 可單程或感應支付',
    cardNotes: [
      'Rabbit Card 主要給 BTS，用 MRT 仍可能要另購票或用感應支付。',
      '曼谷塞車重，跨區優先鐵道，叫車放在短程或深夜。',
      '機場線與 BTS 轉乘動線長，帶行李要多抓時間。'
    ],
    airport: [
      'BKK -> Airport Rail Link：Phaya Thai（轉 BTS）',
      'DMK -> A1/A2 巴士：Mo Chit（轉 BTS/MRT）',
      '深夜抵達建議直接 Grab'
    ],
    lines: [
      'BTS Sukhumvit：Asok、Siam、Mo Chit',
      'BTS Silom：Saphan Taksin、Sala Daeng',
      'MRT Blue：Bang Sue、Asok、Silom'
    ],
    stations: [
      'Asok：BTS 與 MRT 交會，跨區最常轉乘。',
      'Siam：BTS 雙線交會，市中心購物核心。',
      'Sala Daeng：BTS 轉 MRT Silom 常用節點。',
      'Saphan Taksin：銜接昭披耶河船線，跑河岸景點關鍵。'
    ],
    apps: [
      'Google Maps：路線整體規劃與步行導航。',
      'Grab：叫車與機場接送。',
      'ViaBus：即時公車位置，避免久等。'
    ],
    culture: [
      '塞車嚴重，跨區優先 BTS/MRT。',
      '寺廟需注意服裝，肩膀與膝蓋避免裸露。',
      '計程車不一定跳表，叫車 App 較穩。'
    ],
    map: { airportOrigin: '蘇凡納布國際機場', cityDestination: 'Siam' }
  },
  峴港: {
    cards: '無固定交通卡，市區以 Grab/包車為主',
    cardNotes: [
      '峴港多數旅客不需要交通卡，Grab 足夠應付市區行程。',
      '會安、巴拿山這類跨區點，包車/一日團通常更省時省力。',
      '叫車前先確認上車點，景點周邊常有管制區。'
    ],
    airport: [
      'DAD -> 美溪沙灘飯店：Grab 約 15-20 分鐘',
      'DAD -> 韓江市區：Grab 約 10-15 分鐘'
    ],
    lines: [
      '市區點對點：Grab 汽車/機車',
      '會安、巴拿山：一日團或包車最省時'
    ],
    stations: [
      '峴港機場 DAD：到市區與回程最重要出入口。',
      '韓市場周邊：市中心購物與換匯熱區。',
      '美溪沙灘周邊：海灘住宿密集，晚間移動頻繁。'
    ],
    apps: [
      'Grab：市區與景點點對點叫車主力。',
      'Google Maps：確認上車點與營業時間。',
      'Klook：會安/巴拿山等一日行程預訂。',
      'KKday：比價在地團與接駁方案。'
    ],
    culture: [
      '機車流量大，過馬路保持固定速度直行。',
      '午後常有陣雨，包包內放輕便雨具。',
      '夜間回程先叫車，避免現場久等。'
    ],
    map: { airportOrigin: '峴港國際機場', cityDestination: '韓市場' }
  },
  河內: {
    cards: '無固定旅客卡，老城區步行 + Grab',
    cardNotes: [
      '河內旅遊以步行 + Grab 為主，不必特別買卡。',
      '跨區通勤時間常受路況影響，行程不要排太滿。',
      '熱門時段叫車等待較久，提早 10-15 分鐘叫車。'
    ],
    airport: [
      'HAN -> 老城區：Grab 約 40-60 分鐘',
      'HAN -> 還劍湖：Grab 或飯店接送'
    ],
    lines: [
      '老城區、還劍湖：步行最有效率',
      '跨區移動：Grab',
      '下龍灣/寧平：一日團接送'
    ],
    stations: [
      '河內機場 HAN：進出城關鍵，叫車與接送集合點。',
      '還劍湖：城市地標，往各區移動定位方便。',
      '老城區：美食與咖啡最密集，步行探索核心。'
    ],
    apps: [
      'Grab：主要移動方式，避開路邊喊價。',
      'Google Maps：步行導覽與店家營業資訊。',
      'Klook：下龍灣/寧平行程預訂。',
      'KKday：接駁與一日團備援比價。'
    ],
    culture: [
      '交通節奏快，過馬路跟著人群節奏走。',
      '熱門店家可能不收卡，備少量現金。',
      'Train Street 開放狀態常變，先查當天公告。'
    ],
    map: { airportOrigin: '內排國際機場', cityDestination: '還劍湖' }
  },
  澳門: {
    cards: '以飯店接駁巴士 + 公車 + 計程車為主',
    cardNotes: [
      '澳門旅客多用飯店接駁與公車，通常不需要另辦交通卡。',
      '半島與路氹來回可優先接駁巴士，省下計程車費。',
      '晚間散場時段（演出後）叫車壓力高，先規劃回程。'
    ],
    airport: [
      'MFM -> 路氹飯店：免費接駁巴士最方便',
      '口岸 -> 半島/路氹：接駁巴士或公車'
    ],
    lines: [
      '半島景點：步行 + 公車',
      '半島 <-> 路氹：飯店接駁巴士'
    ],
    stations: [
      '澳門機場 MFM：飯店接駁與入境後首站。',
      '關閘：陸路口岸樞紐，往半島與路氹分流點。',
      '路氹金光大道：大型飯店與演出區移動核心。'
    ],
    apps: [
      'Google Maps：步行與跨區路線參考。',
      '澳門巴士 App：查公車到站與路線轉乘。'
    ],
    culture: [
      '假日人潮大，熱門景點建議早上先跑。',
      '飯店接駁需排隊，請預留等待時間。',
      '餐廳尖峰候位常見，可先訂位。'
    ],
    map: { airportOrigin: '澳門國際機場', cityDestination: '路氹金光大道' }
  },
  香港: {
    cards: '八達通 Octopus（地鐵、公車、便利商店都可用）',
    cardNotes: [
      '八達通幾乎全場景可用，先儲值可加快移動效率。',
      '機場快線與一般港鐵票價差異大，依住宿區決定最省。',
      '尖峰時段換乘站很擠，行李旅客建議避開通勤時段。'
    ],
    airport: [
      'HKG -> 機場快線：香港站、九龍站',
      'HKG -> 機場巴士：可直達多數市區'
    ],
    lines: [
      '荃灣線：尖沙咀、旺角、金鐘',
      '港島線：中環、灣仔、銅鑼灣'
    ],
    stations: [
      '香港站：機場快線終點，接中環商業區最快。',
      '九龍站：西九龍與尖沙咀方向轉乘關鍵。',
      '尖沙咀站：維港與購物區核心站，人流高。',
      '中環站：港島線與商業區樞紐，過海轉乘常用。'
    ],
    apps: [
      'MTR Mobile：官方路線、票價與服務通知。',
      'Google Maps：跨港鐵/步行/巴士整合規劃。',
      'Citymapper：都市轉乘建議與替代路線。'
    ],
    culture: [
      '通勤時段很擠，避開 8:00-9:30 與 18:00-19:30。',
      '熱門餐廳通常需拿號碼牌排隊。',
      '上下手扶梯請依現場指示。'
    ],
    map: { airportOrigin: '香港國際機場', cityDestination: '香港站' }
  },
  新加坡: {
    cards: 'SimplyGo（感應信用卡）或 EZ-Link',
    cardNotes: [
      '短期旅客可直接用感應信用卡搭車，省去買卡流程。',
      '若同行有孩童或無國際卡，再補 EZ-Link 比較穩。',
      '地鐵站內移動距離可能長，轉乘時間要保守估。'
    ],
    airport: [
      'SIN -> MRT：樟宜機場線轉市區',
      'SIN -> 計程車/Grab：多人分攤更省時間'
    ],
    lines: [
      'EW 線：機場轉乘、市中心常用',
      'NS 線：Orchard、City Hall、Marina 區',
      'DT 線：Bugis、Little India'
    ],
    stations: [
      'Changi Airport：入境後轉 MRT/叫車起點。',
      'City Hall：NS/EW 交會，往濱海灣與市中心方便。',
      'Bugis：DT/EW 交會，飯店與商圈密集。',
      'Orchard：購物區主軸站，行程常回訪。'
    ],
    apps: [
      'Citymapper：都會交通最佳化轉乘建議。',
      'Google Maps：全域導航與店家資訊。',
      'Grab：多人或深夜回飯店叫車。'
    ],
    culture: [
      '捷運與公車內禁食禁飲。',
      '法規執行嚴格，公共空間注意標示。',
      '午後常有雷陣雨，包包放折傘。'
    ],
    map: { airportOrigin: '樟宜機場', cityDestination: 'City Hall MRT Station' }
  }
};

export const m4 = {
  async start() {
    return cardAsk(
      '當地交通攻略',
      '選城市，我會給你交通卡、機場進市區、線路站點、常用 App 和注意事項。',
      cityOptions,
      1
    );
  },

  async handleStep({ message }) {
    const raw = textValue(message);
    const city = normalizeCity(raw);
    const guide = transportProfiles[city] ?? fallbackGuide(city || raw || '目的地');
    return done({
      type: 'flex',
      altText: `${city || raw || '目的地'} 交通攻略`,
      contents: transportCarousel(city || raw || '目的地', guide)
    });
  }
};

function normalizeCity(input) {
  const text = String(input || '').trim();
  const lower = text.toLowerCase();
  for (const [city, aliases] of Object.entries(cityAliases)) {
    if (aliases.some((a) => lower === a.toLowerCase())) return city;
  }
  return text;
}

function transportCarousel(city, guide) {
  const noteChunks = chunkList(guide.cardNotes || [], 4);
  return {
    type: 'carousel',
    contents: [
      infoBubble(`${city} 交通攻略`, [sectionText('交通卡', guide.cards)]),
      ...noteChunks.map((chunk, index) =>
        infoBubble(`${city} 卡片注意 ${index + 1}/${noteChunks.length}`, [sectionList('卡片注意', chunk)])
      ),
      infoBubble(`${city} 機場與線路`, [sectionList('機場進市區', guide.airport), sectionList('核心線路', guide.lines)]),
      infoBubble(`${city} 站點與 App`, [sectionList('關鍵站點', guide.stations), sectionList('常用 App', guide.apps)]),
      actionBubble(city, guide)
    ]
  };
}

function infoBubble(title, sections) {
  return {
    type: 'bubble',
    size: 'mega',
    body: {
      type: 'box',
      layout: 'vertical',
      spacing: 'md',
      contents: [{ type: 'text', text: title, weight: 'bold', size: 'xl', wrap: true, color: '#111827' }, ...sections]
    }
  };
}

function actionBubble(city, guide) {
  const origin = guide.map?.airportOrigin || `${city} 機場`;
  const destination = guide.map?.cityDestination || `${city} 市中心`;
  return {
    type: 'bubble',
    size: 'mega',
    body: {
      type: 'box',
      layout: 'vertical',
      spacing: 'md',
      contents: [{ type: 'text', text: `${city} 使用提醒`, weight: 'bold', size: 'xl', wrap: true, color: '#111827' }, sectionList('注意事項', guide.culture)]
    },
    footer: {
      type: 'box',
      layout: 'vertical',
      spacing: 'sm',
      contents: [
        linkButton('機場->市區 大眾運輸', googleMapsDirectionsLink({ origin, destination, travelmode: 'transit' }), '#2563eb'),
        linkButton('交通卡購買與儲值點', googleMapsSearchLink(`${city} 交通卡 購買 儲值`), '#334155'),
        linkButton('官方地鐵路線圖', googleSearchLink(`${city} 地鐵 路線圖 官方`), '#0f766e')
      ]
    }
  };
}

function sectionText(title, text) {
  return {
    type: 'text',
    size: 'md',
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
      { type: 'text', text: title, size: 'md', weight: 'bold', color: '#0f172a' },
      ...items.map((item) => ({
        type: 'text',
        text: `- ${item}`,
        size: 'md',
        color: '#374151',
        wrap: true
      }))
    ]
  };
}

function chunkList(items, size) {
  const result = [];
  for (let i = 0; i < items.length; i += size) result.push(items.slice(i, i + size));
  return result;
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
    cardNotes: [
      '短期旅客先確認卡片有效期、是否可退餘額、遺失能否補發。',
      '跨區搭乘前確認同一張卡是否支援，避免出站補票。'
    ],
    airport: ['優先選機場快線、機場巴士或官方叫車點。', '深夜抵達先用叫車 App 或飯店接送。'],
    lines: ['先鎖定住宿附近 1-2 條主線，不要一開始就買太多 pass。'],
    stations: [`${city} 主車站：跨區移動與行李轉乘核心。`, `${city} 市中心轉乘站：串接主要景點最有效率。`],
    apps: ['Google Maps：全程導航與步行銜接。', '當地叫車 App：夜間與行李移動備援。', '官方地鐵/公車 App：即時班次與停駛資訊。'],
    culture: ['尖峰時段預留排隊時間。', '先看車廂禁食/行李規則。', '夜間回程先查末班車時間。'],
    map: { airportOrigin: `${city} 機場`, cityDestination: `${city} 市中心` }
  };
}
