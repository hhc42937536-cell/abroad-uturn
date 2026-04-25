import { googleMapsSearchLink, googleSearchLink } from '../services/deepLinks.js';
import { env } from '../config/env.js';
import { loadTrendProfiles } from '../services/trendFeed.js';
import { cardAsk, textValue } from './shared.js';
import { popularDestinations } from './options.js';

const cityOptions = popularDestinations.slice(0, 11);

const cityAliases = {
  東京: ['東京', 'tokyo', '日本'],
  大阪: ['大阪', 'osaka', '關西'],
  首爾: ['首爾', 'seoul', '韓國', '首爾市'],
  曼谷: ['曼谷', 'bangkok', '泰國'],
  香港: ['香港', 'hong kong', 'hk'],
  新加坡: ['新加坡', 'singapore', 'sg'],
  福岡: ['福岡', 'fukuoka'],
  沖繩: ['沖繩', '沖縄', 'okinawa', '那霸'],
  吉隆坡: ['吉隆坡', 'kuala lumpur', 'kl', '馬來西亞'],
  胡志明市: ['胡志明市', '胡志明', 'ho chi minh', 'saigon', '西貢'],
  馬尼拉: ['馬尼拉', 'manila', '菲律賓']
};

export const defaultTrendProfiles = {
  東京: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：NewYork Perfect Cheese、PRESS BUTTER SAND、Tokyo Banana 地區限定款',
      '小家電：ReFa 吹風機/電棒、Panasonic 美容家電、BicCamera 免稅熱門機種',
      '生活選物：loft、Hands、3COINS 聯名與季節限定小物'
    ],
    hotSpots: [
      '東京迪士尼海洋 Fantasy Springs（2024 開幕後持續爆滿）',
      'teamLab Borderless（麻布台新館）',
      '麻布台 Hills / 豐洲新商場群（高討論新區域）'
    ],
    hotPlans: [
      '玩法 A：teamLab -> 麻布台 -> 六本木/東京鐵塔夜景',
      '玩法 B：迪士尼海洋全天 + 晚上回市區補藥妝',
      '玩法 C：銀座百貨掃貨 + 秋葉原小家電一次買齊'
    ],
    caution: [
      '熱門點預約先搶：迪士尼、teamLab 都建議先訂時段票。',
      '小家電電壓與保固先確認，避免買回台灣無法完整使用。'
    ],
    mapQuery: '東京 最新景點 商場',
    officialLabel: 'Fantasy Springs 官方',
    officialUri: 'https://www.tokyodisneyresort.jp/special/en/fantasysprings/'
  },
  大阪: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：551 蓬萊、呼吸巧克力、堂島點心、限定 KitKat',
      '藥妝與小家電：難波/梅田大店比價後一次買',
      '球鞋潮流：美國村與心齋橋聯名款更新快'
    ],
    hotSpots: [
      'USJ 超級任天堂世界 Donkey Kong 區（2024 後高熱度）',
      'Grand Green Osaka（梅田新區）',
      'teamLab Botanical Garden Osaka（夜間光影）'
    ],
    hotPlans: [
      '玩法 A：USJ 全天 -> 梅田晚餐夜景',
      '玩法 B：心齋橋掃貨 -> 道頓堀美食 -> 新世界夜拍',
      '玩法 C：大阪市區 + 京都半日快閃'
    ],
    caution: [
      'USJ 旺日人潮極高，建議 Express Pass 或開園即進場。',
      '梅田站系統複雜，轉乘預留至少 15 分鐘。'
    ],
    mapQuery: '大阪 最新景點 2026',
    officialLabel: 'USJ 官方資訊',
    officialUri: 'https://www.usj.co.jp/web/en/us'
  },
  首爾: {
    updated: '2026-04',
    hotBuys: [
      '美妝保養：Olive Young 熱銷榜（修護、提亮、舒緩類）',
      '香氛穿搭：Tamburins、Matin Kim、emis 等聖水洞熱門品牌',
      '照片體驗：弘大/延南韓式大頭照（證件照與形象照）'
    ],
    hotSpots: [
      '聖水洞快閃店與選物街區（更新速度快）',
      'The Hyundai Seoul（品牌快閃與話題展）',
      '首爾林-漢江線路（城市散步新玩法）'
    ],
    hotPlans: [
      '玩法 A：上午皮膚管理 -> 下午韓式大頭照 -> 晚上弘大',
      '玩法 B：聖水洞品牌巡店 -> 漢江夜景 -> 便利商店宵夜',
      '玩法 C：明洞採購 -> 江南醫美諮詢/保養療程'
    ],
    caution: [
      '醫美務必選有執照醫師與正規診所，先做術前諮詢與禁忌評估。',
      '不要當天連做多項高刺激療程，行程要留恢復時間。'
    ],
    mapQuery: '首爾 聖水洞 快閃店',
    officialLabel: '首爾市路線圖',
    officialUri: 'https://english.seoul.go.kr/service/movement/route-map/'
  },
  曼谷: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：手標泰奶、泰式香氛、皇家蜂蜜/草本系列',
      '彩妝零食：7-11/Big C 熱銷清單（小額多樣最容易爆買）',
      '服飾包袋：恰圖恰與設計師市集品牌'
    ],
    hotSpots: [
      'One Bangkok（2024 開幕後持續熱門）',
      'EMSPHERE + EmQuartier 商圈串聯',
      '昭披耶河畔夜市與河景餐廳升溫'
    ],
    hotPlans: [
      '玩法 A：One Bangkok -> 四面佛 -> 夜市按摩',
      '玩法 B：恰圖恰掃貨 -> 河畔夜景 -> Rooftop bar',
      '玩法 C：咖啡館巡禮 + 泰式 SPA + 夜間市集'
    ],
    caution: [
      '曼谷交通壅塞，跨區移動盡量靠 BTS/MRT。',
      '熱門按摩店先預約，現場排隊常超過 1 小時。'
    ],
    mapQuery: '曼谷 One Bangkok Emsphere',
    officialLabel: 'One Bangkok 官方',
    officialUri: 'https://www.onebangkok.com/'
  },
  香港: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：曲奇、蛋捲、港式奶茶包、特色茶餐廳周邊',
      '潮流購物：尖沙咀/銅鑼灣運動與街頭品牌',
      '藥妝：萬寧/屈臣氏限定組合與旅行裝'
    ],
    hotSpots: [
      '西九文化區（M+、故宮）長期高討論',
      'K11 MUSEA 與尖沙咀海旁夜景線',
      '啟德體育園周邊活動檔期（演出/賽事）'
    ],
    hotPlans: [
      '玩法 A：中環半日散步 -> 山頂夜景',
      '玩法 B：西九展館 -> 尖沙咀維港夜拍',
      '玩法 C：港島咖啡店巡禮 + 晚上蘭桂坊'
    ],
    caution: [
      '熱門餐廳候位時間長，晚餐建議先訂位。',
      '活動檔期住宿價差大，先看演唱會/賽事日曆。'
    ],
    mapQuery: '香港 西九 K11 啟德',
    officialLabel: '港鐵系統圖官方',
    officialUri: 'https://www.mtr.com.hk/en/customer/services/system_map.html'
  },
  新加坡: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：Bacha Coffee、TWG、斑蘭/咖椰醬',
      '機場限定：星耀樟宜與精品超市伴手禮組',
      '潮流品牌：烏節路與濱海灣快閃店'
    ],
    hotSpots: [
      'Sentosa Sensoryscape（新加坡近年話題夜間散步線）',
      'Bird Paradise（Mandai 新園區）',
      '濱海灣活動與展演檔期持續高熱度'
    ],
    hotPlans: [
      '玩法 A：白天動物園系統 -> 晚上濱海灣燈光',
      '玩法 B：烏節購物 -> 牛車水晚餐 -> 克拉碼頭',
      '玩法 C：聖淘沙半日 + 晚上機場星耀收尾'
    ],
    caution: [
      '餐廳尖峰時段排隊長，熱門店建議離峰用餐。',
      '規範較嚴，公共場所違規成本高。'
    ],
    mapQuery: '新加坡 Sentosa Sensoryscape Bird Paradise',
    officialLabel: 'LTA MRT 官方圖',
    officialUri: 'https://www.lta.gov.sg/content/dam/ltagov/getting_around/public_transport/rail_network/pdf/SM_TEL4_Ch_%28Ver150824%29_TL.pdf'
  },
  福岡: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：明太子系產品、博多通饅頭、草莓甜點',
      '藥妝與家居：博多站/天神商圈一次補貨',
      '在地食材：一蘭限定、辣明太相關調理包'
    ],
    hotSpots: [
      'teamLab Forest Fukuoka',
      'LaLaport 福岡 + 巨型鋼彈地標',
      '糸島海岸線咖啡店與景觀點'
    ],
    hotPlans: [
      '玩法 A：博多購物 -> 中洲屋台 -> 運河城夜景',
      '玩法 B：市區半日 + 太宰府/糸島一日線',
      '玩法 C：親子走 teamLab + 海之中道'
    ],
    caution: [
      '週末糸島交通較滿，包車或提早出發更穩。',
      '屋台熱門店夜間排隊常見。'
    ],
    mapQuery: '福岡 最新景點 teamLab Forest',
    officialLabel: '福岡觀光官方',
    officialUri: 'https://yokanavi.com/en/'
  },
  沖繩: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：紅芋塔、雪鹽、沖繩黑糖、ORION 啤酒周邊',
      '藥妝與零食：國際通 Don Quijote 一次打包',
      '海鹽/香氛：沖繩自然系品牌熱門'
    ],
    hotSpots: [
      'JUNGLIA（2025 開幕後持續話題）',
      '瀨長島 Umikaji Terrace 日落線',
      '北部海岸線自駕景點持續熱門'
    ],
    hotPlans: [
      '玩法 A：南部景點 + 國際通夜逛',
      '玩法 B：北部自然線 + 美麗海周邊',
      '玩法 C：海邊咖啡 + Outlet 採買'
    ],
    caution: [
      '沖繩以自駕為主，雨天/旺日移動時間要放寬。',
      '熱門餐廳與景點停車位有限，先抓抵達時段。'
    ],
    mapQuery: '沖繩 JUNGLIA 國際通',
    officialLabel: '沖繩觀光官方',
    officialUri: 'https://visitokinawajapan.com/'
  },
  吉隆坡: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：Beryl\'s 巧克力、白咖啡、榴槤加工零食',
      '穆斯林友善美妝與生活用品近年討論高',
      '百貨掃貨：TRX 與 Pavilion 雙區比價'
    ],
    hotSpots: [
      'The Exchange TRX（新商圈）',
      'Merdeka 118 周邊城市地景',
      '鬼仔巷與茨廠街夜間街區更新'
    ],
    hotPlans: [
      '玩法 A：TRX -> Pavilion -> 夜市',
      '玩法 B：黑風洞半日 + 市中心咖啡線',
      '玩法 C：城市觀景台 + 酒吧夜景'
    ],
    caution: [
      '午後雷陣雨常見，行程要有室內備案。',
      '不同商圈車程差很大，跨區一天不要排太滿。'
    ],
    mapQuery: 'Kuala Lumpur TRX Merdeka 118',
    officialLabel: 'TRX 官方',
    officialUri: 'https://www.theexchange.my/'
  },
  胡志明市: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：越南咖啡豆、腰果、可可與在地手作',
      '平價服飾與鞋包：阮惠街/濱城市場周邊',
      '香氛與家居小物：新商場選物店熱度上升'
    ],
    hotSpots: [
      '胡志明市捷運 1 號線開通後沿線玩法升溫',
      '西貢河岸與新城區夜景線',
      '咖啡公寓與設計選物店持續高流量'
    ],
    hotPlans: [
      '玩法 A：市區咖啡巡禮 + 濱城市場買手信',
      '玩法 B：沿捷運線玩景點 + 夜晚河岸',
      '玩法 C：法式建築散步 + 夜間按摩'
    ],
    caution: [
      '路口機車量大，過馬路保持節奏不要折返。',
      '換匯與刷卡匯率差異大，先比較再大額消費。'
    ],
    mapQuery: 'Ho Chi Minh Metro Line 1 attractions',
    officialLabel: '胡志明市捷運地圖參考',
    officialUri: 'https://hochiminhcitymetro.com/maps/'
  },
  馬尼拉: {
    updated: '2026-04',
    hotBuys: [
      '伴手禮：7D 芒果乾、Ube Jam、香蕉脆片、椰子零食',
      '美式與街頭品牌：BGC / Makati 商圈最齊',
      '在地甜點與咖啡品牌周邊近年很受歡迎'
    ],
    hotSpots: [
      'BGC 藝術街區與咖啡館',
      'Intramuros 夜間導覽與文化路線',
      '灣區大型娛樂場館與夜間表演'
    ],
    hotPlans: [
      '玩法 A：BGC 一日生活圈（購物+咖啡+酒吧）',
      '玩法 B：舊城區文化線 + Mall of Asia 夜景',
      '玩法 C：短程跳島或近郊自然日遊'
    ],
    caution: [
      '尖峰交通壅塞嚴重，跨區移動要抓緩衝。',
      '夜間回程建議使用可信任叫車平台。'
    ],
    mapQuery: 'Manila BGC Intramuros itinerary',
    officialLabel: '菲律賓觀光官方',
    officialUri: 'https://www.tourism.gov.ph/'
  }
};

const cityDeepDetails = {
  東京: {
    hotBuys: [
      '零食：N.Y.C. Sand、薯條三兄弟、Tokyo Campanella、Royce 生巧（機場限定）',
      '藥妝：EVE、合利他命、參天眼藥水、休足時間（價格帶差異大）',
      '扭蛋/動漫：池袋 Sunshine、秋葉原 Radio Kaikan、中野 Broadway',
      '廚房與文具：合羽橋道具街、銀座伊東屋、Loft 季節聯名'
    ],
    hotSpots: [
      '澀谷 Sakura Stage（新商業區）',
      '豐洲千客萬來（市場+溫泉+美食）',
      '哈利波特影城（練馬）',
      '麻布台 Hills 展演與觀景動線'
    ],
    hotPlans: [
      '早班機玩法：淺草->上野阿美橫町->秋葉原採買',
      '雨天玩法：池袋 Sunshine->室內展館->百貨戰利品',
      '親子玩法：迪士尼/哈利波特雙主題二選一',
      '深度玩法：神保町古書街->神田咖啡->東京車站一番街'
    ],
    caution: [
      '熱門甜點常提早完售，建議上午先買再跑景點。',
      '退稅改制與先付後退趨勢增加，結帳時先確認店家流程。'
    ]
  },
  大阪: {
    hotBuys: [
      '甜點：BonbonRococo、呼吸巧克力、堂島捲季節款',
      '零食：章魚燒仙貝、關西限定 Pretz、阪急百貨地下伴手禮',
      '藥妝：梅田/難波比價後一次補貨，價差可達 10% 以上',
      '球鞋潮流：美國村古著與限定鞋款'
    ],
    hotSpots: [
      'Grand Green Osaka 新區展演',
      '中之島美術館周邊新路線',
      '環球 CityWalk 新店更替快',
      '道頓堀沿岸夜間活動檔期'
    ],
    hotPlans: [
      '購物線：梅田百貨群->中崎町咖啡->晚間空中庭園',
      '吃貨線：黑門市場->心齋橋->福島居酒屋',
      '近郊線：大阪市區+神戶港區一日',
      '親子線：USJ 隔日排海遊館減壓'
    ]
  },
  首爾: {
    hotBuys: [
      'K-Beauty：Olive Young 月榜（保濕修護、防曬提亮、急救面膜）',
      '香氛：Tamburins、Nonfiction、Aesop Korea 限定組',
      '服飾：Matin Kim、emis、Mardi Mercredi、Musinsa Standard',
      '便利商店限定：蜂蜜奶油杏仁新口味、聯名飲料與即食包'
    ],
    hotSpots: [
      '聖水洞品牌快閃輪替區（每月更新）',
      'HYBE 周邊與龍山新商圈',
      '汝矣島漢江夜間活動帶',
      '新沙/狎鷗亭醫美密集區'
    ],
    hotPlans: [
      '保養輕療程線：肌膚檢測->保濕管理->低刺激修復',
      '形象線：韓式大頭照->髮妝造型->聖水街拍',
      '購物線：The Hyundai->聖水->弘大夜逛',
      '療程線：術前諮詢日與療程日拆開，避免同日高刺激'
    ],
    medicalTrends: [
      '皮膚管理：水飛梭/清潔管理（恢復期短，適合旅遊中安排）',
      '光電保養：皮秒/光子（術後防曬與保濕要做足）',
      '拉提類：音波/電波（通常先諮詢再安排正式療程）',
      '針劑類：肉毒/玻尿酸（務必確認醫師資歷與產品來源）',
      '痘疤/毛孔：分段療程，不建議臨回國前硬做高刺激',
      '頭皮/髮際管理：近年討論升溫，需評估恢復時間',
      '牙齒美白/貼片：觀光客熱門，但要留回診緩衝',
      '韓式大頭照：拍攝前一天避免高刺激療程造成泛紅'
    ],
    caution: [
      '任何侵入性療程都要確認診所合法、醫師姓名與執照。',
      '療程前確認禁忌藥物、過敏史與術後返台照護方式。'
    ]
  },
  曼谷: {
    hotBuys: [
      '香氛：KARMAKAMET、HARNN、Thann 旅遊組',
      '美妝：Srichand、4U2、Mistine 新系列',
      '超市清單：Big C 必買零食牆與草本藥膏',
      '設計品牌：Siam Center/EMSPHERE 獨立品牌櫃'
    ],
    hotSpots: [
      'One Bangkok 展演區與新餐廳群',
      'EM District 夜間活動',
      '河岸 Asiatique 新檔期',
      'Ari 咖啡街持續升溫'
    ],
    hotPlans: [
      '寺廟+商場雙線：上午大皇宮，下午 One Bangkok',
      '市集+按摩線：恰圖恰->Ari->晚間 Spa',
      '夜景線：ICONSIAM->河景餐廳->Rooftop',
      '雨天線：百貨串聯+室內咖啡廳'
    ]
  },
  香港: {
    hotBuys: [
      '伴手禮：蝴蝶酥、蛋捲、奶茶包、港式醬料',
      '潮牌：銅鑼灣與尖沙咀限定聯名',
      '藥妝：萬寧/屈臣氏組合包與旅行規格',
      '展覽周邊：M+ 設計品與文創選物'
    ],
    hotSpots: [
      '西九文化區活動檔期',
      '啟德體育園大型活動周邊',
      '中環 PMQ/大館文創動線',
      'K11 MUSEA 快閃品牌'
    ],
    hotPlans: [
      '文化線：M+->故宮->尖沙咀海旁',
      '城市線：中環->太平山->蘭桂坊',
      '親子線：迪士尼或海洋公園二選一',
      '夜景線：天星小輪->維港->K11 夜拍'
    ]
  },
  新加坡: {
    hotBuys: [
      '咖啡茶：Bacha、TWG、亞坤/松發伴手禮包',
      '食品：咖椰醬、斑蘭蛋糕、肉骨茶料理包',
      '機場限定：Jewel 品牌禮盒',
      '設計選物：Design Orchard 新加坡品牌'
    ],
    hotSpots: [
      'Sentosa Sensoryscape 夜間路線',
      'Bird Paradise + Mandai 生態區',
      '濱海灣演出季活動',
      '新展館快閃活動'
    ],
    hotPlans: [
      '白天動物園+晚上濱海灣雙重點',
      '烏節購物+克拉碼頭夜生活',
      '牛車水+小印度+阿拉伯街文化線',
      '雨天備案：室內館群與商場串聯'
    ]
  },
  福岡: {
    hotBuys: [
      '明太子品牌比價清單（常溫/冷藏）',
      '博多通りもん與季節甜點',
      '辛子高菜、九州拉麵包',
      '在地咖啡與抹茶點心'
    ],
    hotSpots: [
      'teamLab Forest 新展期',
      'LaLaport 福岡購物路線',
      '糸島新咖啡點',
      '博多站周邊活動市集'
    ],
    hotPlans: [
      '市區吃買線：博多->天神->中洲',
      '近郊線：太宰府或糸島一日',
      '親子線：teamLab + 海之中道',
      '雨天線：地下街+百貨+美食層'
    ]
  },
  沖繩: {
    hotBuys: [
      '紅芋塔各品牌口味比較',
      '雪鹽、黑糖、海葡萄常溫包',
      'ORION 周邊與限定啤酒',
      '沖繩香氛與天然保養小物'
    ],
    hotSpots: [
      'JUNGLIA 主題園區',
      '瀨長島海景步道',
      '北部海岸自駕新點',
      '美國村夜間活動'
    ],
    hotPlans: [
      '南部文化+國際通夜逛',
      '北部自然+美麗海',
      '海邊咖啡+Outlet 採買',
      '雨天改商場與室內館'
    ]
  },
  吉隆坡: {
    hotBuys: [
      'Beryl’s 巧克力新口味',
      '白咖啡/拉茶即沖包',
      '榴槤與熱帶水果加工零食',
      '穆斯林友善美妝用品'
    ],
    hotSpots: [
      'The Exchange TRX 新店',
      'Merdeka 118 周邊路線',
      '鬼仔巷夜間藝術街區',
      'Pavilion 新櫃位'
    ],
    hotPlans: [
      'TRX + Pavilion 雙商圈',
      '黑風洞+市中心咖啡',
      '夜景觀景台+酒吧',
      '雨天商場備案線'
    ]
  },
  胡志明市: {
    hotBuys: [
      '精品咖啡豆與濾掛包',
      '腰果、可可與巧克力',
      '越南手作皮件與編織包',
      '在地香氛與居家小物'
    ],
    hotSpots: [
      '捷運 1 號線周邊玩法',
      '西貢河岸新夜景點',
      '設計選物街區',
      '咖啡公寓新店更替'
    ],
    hotPlans: [
      '咖啡巡禮+市場採買',
      '捷運沿線景點一日',
      '法式建築+夜間河岸',
      '雨天室內商場線'
    ]
  },
  馬尼拉: {
    hotBuys: [
      '芒果乾品牌比價與機場限定',
      'Ube 系列甜點',
      '在地咖啡與可可',
      'BGC 設計品牌小物'
    ],
    hotSpots: [
      'BGC 街區活動',
      'Intramuros 夜導覽',
      'MOA 灣區夜景線',
      'Makati 咖啡與酒吧圈'
    ],
    hotPlans: [
      'BGC 一日生活圈',
      '舊城文化線+灣區夜景',
      '近郊自然日遊',
      '雨天商場與室內娛樂線'
    ]
  }
};

export const m7 = {
  async start() {
    const mode = env.ENABLE_M7_AUTO_REFRESH
      ? '（系統自動更新）'
      : env.M7_TREND_FEED_URL
        ? '（外部來源更新）'
        : '（目前為內建資料）';
    return cardAsk(
      '現在最夯',
      `選城市，直接給你「大家買什麼 + 新景點 + 爆款行程 + 注意事項」${mode}。`,
      cityOptions,
      1
    );
  },

  async handleStep({ message }) {
    const raw = textValue(message);
    const city = normalizeCity(raw);
    const { profiles, source } = await loadTrendProfiles(defaultTrendProfiles);
    const base = profiles[city] ?? fallbackProfile(city || raw || '目的地');
    const profile = enrichProfile(city, base);
    const freshness = freshnessLabel(profile.updated);
    const caution = freshness.isStale
      ? [`資料可能超過 ${env.M7_TREND_MAX_AGE_DAYS} 天未更新，出發前請二次確認。`, ...profile.caution]
      : profile.caution;

    return {
      done: false,
      nextStep: 1,
      state: {},
      messages: [
        {
          type: 'flex',
          altText: `${city} 現在最夯`,
          contents: trendCarousel(city, { ...profile, caution, freshnessText: freshness.text, source })
        },
        cardAsk('還想看哪個城市？', '可連續看 11 城，不用重開功能。', cityOptions, 1).messages[0]
      ]
    };
  }
};

function normalizeCity(input) {
  const text = String(input || '').trim();
  const lower = text.toLowerCase();
  for (const [city, aliases] of Object.entries(cityAliases)) {
    if (aliases.some((alias) => lower === alias.toLowerCase())) return city;
  }
  return text;
}

function trendCarousel(city, profile) {
  const sourceLabel = profile.source === 'auto'
    ? '系統自動抓取'
    : profile.source === 'remote'
      ? '外部更新來源'
      : '內建資料';
  const bubbles = [
    infoBubble(`${city} 最夯摘要`, [
      sectionText('資料時間', `${profile.updated}（${profile.freshnessText}）`),
      sectionText('資料來源', sourceLabel),
      sectionList('這波最紅', profile.hotSpots.slice(0, 3))
    ]),
    ...categoryBubbles(city, '大家都買', '熱門清單', profile.hotBuys, 4),
    ...categoryBubbles(city, '熱門景點', '新點與話題點', profile.hotSpots, 4),
    ...categoryBubbles(city, '爆款玩法', '行程模板', profile.hotPlans, 4)
  ];

  if (Array.isArray(profile.medicalTrends) && profile.medicalTrends.length) {
    bubbles.push(...categoryBubbles(city, '醫美/形象管理', '療程與安排', profile.medicalTrends, 4));
  }

  bubbles.push(actionBubble(city, profile));

  return {
    type: 'carousel',
    contents: bubbles.slice(0, 12)
  };
}

function categoryBubbles(city, title, sectionTitle, items, size = 4) {
  const chunks = chunkList(items || [], size);
  return chunks.map((chunk, index) => infoBubble(
    `${city} ${title}${chunks.length > 1 ? ` ${index + 1}/${chunks.length}` : ''}`,
    [sectionList(sectionTitle, chunk)]
  ));
}

function infoBubble(title, sections) {
  return {
    type: 'bubble',
    size: 'mega',
    body: {
      type: 'box',
      layout: 'vertical',
      spacing: 'md',
      contents: [
        { type: 'text', text: title, weight: 'bold', size: 'xl', wrap: true, color: '#111827' },
        ...sections
      ]
    }
  };
}

function actionBubble(city, profile) {
  return {
    type: 'bubble',
    size: 'mega',
    body: {
      type: 'box',
      layout: 'vertical',
      spacing: 'md',
      contents: [
        { type: 'text', text: `${city} 注意事項`, weight: 'bold', size: 'xl', wrap: true, color: '#111827' },
        sectionList('避免踩雷', profile.caution)
      ]
    },
    footer: {
      type: 'box',
      layout: 'vertical',
      spacing: 'sm',
      contents: [
        linkButton('熱門點地圖', googleMapsSearchLink(profile.mapQuery), '#2563eb'),
        linkButton(profile.officialLabel, profile.officialUri, '#0f766e'),
        linkButton('即時熱搜關鍵字', googleSearchLink(`${city} 2026 必買 新景點`), '#334155')
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

function linkButton(label, uri, color = '#2563eb') {
  return { type: 'button', style: 'primary', color, height: 'sm', action: { type: 'uri', label, uri } };
}

function fallbackProfile(city) {
  return {
    updated: '2026-04',
    hotBuys: [
      `${city} 熱門伴手禮與藥妝清單`,
      `${city} 社群高討論零食與生活小物`,
      `${city} 百貨/市場最常回購品項`,
      `${city} 在地品牌聯名與季節限定`,
      `${city} 交通站/機場高回購清單`
    ],
    hotSpots: [
      `${city} 新開景點與新商場`,
      `${city} 近期社群高討論拍照點`,
      `${city} 夜間活動密集區`,
      `${city} 雨天可改排室內展館`,
      `${city} 地標周邊新玩法`
    ],
    hotPlans: [
      `${city} 購物 + 美食 + 夜景一日線`,
      `${city} 新景點半日 + 在地市場半日`,
      `${city} 雨天室內備案行程`,
      `${city} 早出晚歸高效率玩法`,
      `${city} 親子或長輩友善慢遊線`
    ],
    caution: [
      '熱門名店先預約，避免現場排隊失控。',
      '看清退稅與退貨規則再大量採買。'
    ],
    mapQuery: `${city} 熱門景點`,
    officialLabel: `${city} 觀光官方資訊`,
    officialUri: googleSearchLink(`${city} tourism official`)
  };
}

function enrichProfile(city, profile) {
  const detail = cityDeepDetails[city] ?? {};
  return {
    ...profile,
    hotBuys: mergeUnique(profile.hotBuys, detail.hotBuys, 8),
    hotSpots: mergeUnique(profile.hotSpots, detail.hotSpots, 8),
    hotPlans: mergeUnique(profile.hotPlans, detail.hotPlans, 8),
    caution: mergeUnique(profile.caution, detail.caution, 6),
    medicalTrends: mergeUnique(profile.medicalTrends, detail.medicalTrends, 8)
  };
}

function mergeUnique(primary, secondary, limit) {
  const a = Array.isArray(primary) ? primary : [];
  const b = Array.isArray(secondary) ? secondary : [];
  return [...new Set([...a, ...b])].filter(Boolean).slice(0, limit);
}

function chunkList(items, size) {
  const source = Array.isArray(items) ? items : [];
  if (!source.length) return [[]];
  const result = [];
  for (let index = 0; index < source.length; index += size) result.push(source.slice(index, index + size));
  return result;
}

function freshnessLabel(updated) {
  const parsed = parseUpdatedDate(updated);
  if (!parsed) return { text: '日期格式不明', isStale: true };
  const days = Math.floor((Date.now() - parsed.getTime()) / 86400000);
  if (days <= env.M7_TREND_MAX_AGE_DAYS) return { text: `近 ${days} 天`, isStale: false };
  return { text: `約 ${days} 天前`, isStale: true };
}

function parseUpdatedDate(value) {
  const text = String(value || '').trim();
  if (!text) return null;
  if (/^\d{4}-\d{2}$/.test(text)) {
    const date = new Date(`${text}-01T00:00:00+08:00`);
    return Number.isNaN(date.getTime()) ? null : date;
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    const date = new Date(`${text}T00:00:00+08:00`);
    return Number.isNaN(date.getTime()) ? null : date;
  }
  const date = new Date(text);
  return Number.isNaN(date.getTime()) ? null : date;
}
