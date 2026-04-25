import { getExchangeRate } from '../services/exchangeRate.js';
import { cardAsk, done, textValue } from './shared.js';

const countries = [
  { label: '日本 JPY', value: '日本|JPY', visa: '台灣護照短期觀光免簽，仍需確認護照效期與入境規定。', plugs: 'A 型插座，電壓 100V。' },
  { label: '韓國 KRW', value: '韓國|KRW', visa: '台灣旅客短期觀光通常免簽，但 K-ETA/入境規定可能調整，出發前再確認。', plugs: 'C/F 型插座，電壓 220V。' },
  { label: '泰國 THB', value: '泰國|THB', visa: '台灣旅客觀光入境規定常調整，出發前確認最新免簽天數。', plugs: 'A/B/C/O 型常見，建議帶萬用轉接頭。' },
  { label: '越南 VND', value: '越南|VND', visa: '台灣護照通常需要簽證或電子簽，請先辦妥再訂最後行程。', plugs: 'A/C/G 型常見，建議帶萬用轉接頭。' },
  { label: '香港/澳門 HKD', value: '香港/澳門|HKD', visa: '台灣旅客短期停留通常可入境，仍需確認證件與入境規定。', plugs: 'G 型插座，電壓 220V。' },
  { label: '新加坡 SGD', value: '新加坡|SGD', visa: '短期觀光通常免簽，入境前需留意 SG Arrival Card。', plugs: 'G 型插座，電壓 230V。' },
  { label: '美國 USD', value: '美國|USD', visa: '通常需 ESTA 或簽證，請確認護照、ESTA 狀態與轉機規定。', plugs: 'A/B 型插座，電壓 120V。' },
  { label: '歐洲 EUR', value: '歐洲|EUR', visa: '申根短期免簽規定仍需確認，留意 ETIAS 上線狀態。', plugs: '多為 C/F 型，英國為 G 型。' }
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
      ? `匯率參考：1 TWD 約 ${fx.rate.toFixed(4)} ${currency}（${fx.provider}）`
      : `匯率暫時抓不到，出發前請再用銀行或換匯 App 確認 ${currency}。`;

    return done({
      type: 'text',
      text: [
        `${country} 行前必知`,
        '',
        `簽證/入境：${profile.visa}`,
        rateText,
        `插座：${profile.plugs}`,
        '網路：臨時出發建議先買 eSIM，落地後再視需求補實體 SIM。',
        '現金：先準備第一天交通、餐費與小額現金，其餘用信用卡/提款卡備援。',
        '打包：護照、信用卡、保險、訂房訂票截圖、轉接頭、常備藥、行動電源。',
        '提醒：政策會變，出發前一天請再確認航空公司與官方入境資訊。'
      ].join('\n')
    });
  }
};
