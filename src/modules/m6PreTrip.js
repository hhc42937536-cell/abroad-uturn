import { getExchangeRate } from '../services/exchangeRate.js';
import { mainMenuFlex } from '../views/flex/mainMenu.js';
import { cardAsk, done, textValue } from './shared.js';

const countries = [
  { label: '日本 JPY', value: '日本|JPY', visa: '台灣護照短期觀光免簽，確認護照效期與入境規定。', plugs: 'A 型 / 100V' },
  { label: '韓國 KRW', value: '韓國|KRW', visa: '短期觀光通常免簽，K-ETA/入境規定可能調整，出發前再確認。', plugs: 'C/F 型 / 220V' },
  { label: '泰國 THB', value: '泰國|THB', visa: '觀光入境規定常調整，出發前確認最新免簽天數。', plugs: 'A/B/C/O 型，建議萬用轉接頭' },
  { label: '越南 VND', value: '越南|VND', visa: '台灣護照通常需要簽證或電子簽，先辦妥再訂最後行程。', plugs: 'A/C/G 型，建議萬用轉接頭' },
  { label: '香港/澳門 HKD', value: '香港/澳門|HKD', visa: '短期停留通常可入境，仍需確認證件與入境規定。', plugs: 'G 型 / 220V' },
  { label: '新加坡 SGD', value: '新加坡|SGD', visa: '短期觀光通常免簽，入境前需留意 SG Arrival Card。', plugs: 'G 型 / 230V' },
  { label: '美國 USD', value: '美國|USD', visa: '通常需 ESTA 或簽證，確認護照、ESTA 狀態與轉機規定。', plugs: 'A/B 型 / 120V' },
  { label: '歐洲 EUR', value: '歐洲|EUR', visa: '申根短期免簽規定仍需確認，留意 ETIAS 上線狀態。', plugs: '多為 C/F 型；英國為 G 型' }
];

export const m6 = {
  async start() {
    return cardAsk(
      '行前必知',
      '選國家/地區，我會整理簽證、匯率、插座、網路、打包和入境注意事項。',
      countries,
      1
    );
  },

  async handleStep({ message }) {
    const [country, currencyInput] = textValue(message).split('|');
    const profile = countries.find((item) => item.value.startsWith(country)) ?? countries[0];
    const currency = (currencyInput || profile.value.split('|')[1]).toUpperCase();
    const fx = await getExchangeRate('TWD', currency);
    const rateText = fx.rate
      ? `1 TWD ≈ ${fx.rate.toFixed(4)} ${currency}（${fx.provider}）`
      : `暫時抓不到，出發前請用銀行或換匯 App 確認 ${currency}。`;

    return done([preTripFlex(country, profile, rateText, currency), mainMenuFlex()]);
  }
};

function preTripFlex(country, profile, rateText, currency) {
  return {
    type: 'flex',
    altText: `${country} 行前必知`,
    contents: {
      type: 'bubble',
      size: 'mega',
      header: {
        type: 'box',
        layout: 'vertical',
        backgroundColor: '#1A1F3A',
        paddingAll: '16px',
        contents: [
          { type: 'text', text: `🌏 ${country} 行前必知`, weight: 'bold', size: 'lg', color: '#FFFFFF' },
          { type: 'text', text: '出發前確認以下資訊', size: 'xs', color: '#AAB4D4', margin: 'xs' }
        ]
      },
      body: {
        type: 'box',
        layout: 'vertical',
        spacing: 'md',
        paddingAll: '16px',
        contents: [
          infoRow('📋', '簽證 / 入境', profile.visa),
          infoRow('💱', `匯率（${currency}）`, rateText),
          infoRow('🔌', '插座 / 電壓', profile.plugs),
          separator(),
          infoRow('📶', '網路', '臨時出發建議先買 eSIM，落地後再補實體 SIM。'),
          infoRow('💵', '現金', '先備第一天交通餐費與零錢，其餘刷卡/提款卡備援。'),
          infoRow('🎒', '打包清單', '護照、信用卡、保險、訂單截圖、轉接頭、常備藥、行動電源。'),
          separator(),
          {
            type: 'text',
            text: '⚠️ 政策會變，出發前一天請再確認航空公司與官方入境資訊。',
            size: 'xs',
            color: '#ef4444',
            wrap: true
          }
        ]
      }
    }
  };
}

function infoRow(icon, label, value) {
  return {
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
          { type: 'text', text: label, size: 'sm', weight: 'bold', color: '#1A1F3A', flex: 0 }
        ]
      },
      { type: 'text', text: value, size: 'sm', color: '#374151', wrap: true, margin: 'xs' }
    ]
  };
}

function separator() {
  return { type: 'separator', margin: 'sm' };
}
