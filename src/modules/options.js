export const taiwanAirports = [
  { label: '桃園 TPE', value: 'TPE', city: '台北', note: '國際線最多，適合大多數出國行程。' },
  { label: '松山 TSA', value: 'TSA', city: '台北', note: '市區交通方便，適合東京、首爾、上海等短程航線。' },
  { label: '高雄 KHH', value: 'KHH', city: '高雄', note: '南部出發首選，前往日本、韓國、東南亞都方便。' },
  { label: '台中 RMQ', value: 'RMQ', city: '台中', note: '中部旅客省去北上時間，適合區域航線。' },
  { label: '台南 TNN', value: 'TNN', city: '台南', note: '適合台南與周邊旅客，航線較少但進出省時。' }
];

export const quickTripPresets = [
  { label: '東京3天', value: '東京3天', destination: '東京', region: '東亞', days: '3天', mustVisit: '淺草、晴空塔、澀谷、銀座' },
  { label: '首爾3天', value: '首爾3天', destination: '首爾', region: '東亞', days: '3天', mustVisit: '弘大、明洞、景福宮、聖水洞' },
  { label: '大阪4天', value: '大阪4天', destination: '大阪', region: '東亞', days: '4天', mustVisit: '道頓堀、環球影城、京都一日遊' },
  { label: '曼谷5天', value: '曼谷5天', destination: '曼谷', region: '東南亞', days: '5天', mustVisit: '恰圖恰、市集、按摩、咖啡廳' },
  { label: '沖繩4天', value: '沖繩4天', destination: '沖繩', region: '東亞', days: '4天', mustVisit: '美麗海水族館、國際通、古宇利島' },
  { label: '香港3天', value: '香港3天', destination: '香港', region: '東亞', days: '3天', mustVisit: '中環、尖沙咀、迪士尼、茶餐廳' }
];

export const popularDestinations = [
  { label: '東京', value: '東京', country: '日本', airport: 'NRT', currency: 'JPY', icon: '🗼' },
  { label: '大阪', value: '大阪', country: '日本', airport: 'KIX', currency: 'JPY', icon: '🏯' },
  { label: '首爾', value: '首爾', country: '韓國', airport: 'ICN', currency: 'KRW', icon: '🎵' },
  { label: '曼谷', value: '曼谷', country: '泰國', airport: 'BKK', currency: 'THB', icon: '🛺' },
  { label: '香港', value: '香港', country: '香港', airport: 'HKG', currency: 'HKD', icon: '🌃' },
  { label: '新加坡', value: '新加坡', country: '新加坡', airport: 'SIN', currency: 'SGD', icon: '🌿' },
  { label: '福岡', value: '福岡', country: '日本', airport: 'FUK', currency: 'JPY', icon: '🍜' },
  { label: '沖繩', value: '沖繩', country: '日本', airport: 'OKA', currency: 'JPY', icon: '🏖️' },
  { label: '吉隆坡', value: '吉隆坡', country: '馬來西亞', airport: 'KUL', currency: 'MYR', icon: '🌆' },
  { label: '胡志明市', value: '胡志明市', country: '越南', airport: 'SGN', currency: 'VND', icon: '🛵' },
  { label: '馬尼拉', value: '馬尼拉', country: '菲律賓', airport: 'MNL', currency: 'PHP', icon: '🌊' },
  { label: '峇里島', value: '峇里島', country: '印尼', airport: 'DPS', currency: 'IDR', icon: '🌺' }
];

export const popularRoutes = popularDestinations.map((item) => ({
  label: `${item.label} ${item.airport}`,
  value: item.airport,
  city: item.value
}));

export const popularCountries = [
  { label: '日本 JPY', value: '日本|JPY', visa: '台灣旅客短期觀光免簽，仍需確認護照效期與入境規定。' },
  { label: '韓國 KRW', value: '韓國|KRW', visa: '短期觀光通常免簽，出發前確認 K-ETA 是否暫停或恢復要求。' },
  { label: '泰國 THB', value: '泰國|THB', visa: '台灣旅客入境規定會調整，出發前確認最新免簽天數。' },
  { label: '香港 HKD', value: '香港|HKD', visa: '台灣旅客可持台胞證或符合規定證件入境，先確認證件效期。' },
  { label: '新加坡 SGD', value: '新加坡|SGD', visa: '通常免簽，入境前需填寫 SG Arrival Card。' },
  { label: '美國 USD', value: '美國|USD', visa: '需 ESTA 或簽證，請預留審核時間。' },
  { label: '歐洲 EUR', value: '歐洲|EUR', visa: '申根短期旅遊多為免簽，仍需確認 ETIAS 等新制上路狀態。' }
];

export const lodgingTypes = ['飯店', '公寓式酒店', '青年旅館', '親子飯店', '溫泉旅館', '設計旅店'];
export const lodgingAreas = ['交通最方便', '夜生活熱鬧', '安靜安全', '購物方便', '靠近景點', '預算友善'];
export const trendCategories = ['美食', '拍照打卡', '購物', '親子玩法', '自然景點', '夜生活'];
export const eventTypes = ['演唱會', '見面會', 'Showcase', '音樂節', '頒獎典禮'];
export const budgetOptions = ['低 <3萬', '中 3~6萬', '高 >6萬'];
export const styleOptions = ['自然', '文化', '美食', '購物', '混合', '追星', '親子'];
export const lodgingPreferences = ['交通優先', '飯店舒適', '預算優先', '設計感', '親子友善', '靠近景點'];
export const specialNeedsOptions = ['無', '素食', '帶小孩', '無障礙需求', '長輩同行', '需要慢步調'];

export const popularArtists = [
  'BLACKPINK',
  'BTS',
  'TWICE',
  'NewJeans',
  'SEVENTEEN',
  'aespa',
  'IVE',
  'LE SSERAFIM',
  'Stray Kids',
  'ENHYPEN',
  'IU',
  'Taylor Swift'
];

export function optionValues(items) {
  return items.map((item) => typeof item === 'string' ? item : item.value);
}
