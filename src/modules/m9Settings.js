import { updateUserSettings } from '../repositories/userRepository.js';
import { cardAsk, done, parseCount, quickAsk, textValue } from './shared.js';

const taiwanAirports = [
  { label: '桃園 TPE', value: 'TPE', city: '台北' },
  { label: '松山 TSA', value: 'TSA', city: '台北' },
  { label: '高雄 KHH', value: 'KHH', city: '高雄' },
  { label: '台中 RMQ', value: 'RMQ', city: '台中' },
  { label: '台南 TNN', value: 'TNN', city: '台南' }
];

const currencyOptions = ['TWD', 'JPY', 'KRW', 'THB', 'VND', 'HKD', 'SGD', 'USD', 'EUR'];
const travelerOptions = ['1人', '2人', '3人', '4人', '5人以上'];
const languageOptions = ['繁體中文', 'English', '日本語'];

export const m9 = {
  async start() {
    return cardAsk(
      '設定',
      '先設定預設出發機場，之後查機票、排行程、估預算都會直接套用。',
      taiwanAirports.map((airport) => ({
        label: airport.label,
        value: `${airport.city}|${airport.value}`,
        displayText: `設定 ${airport.label}`
      })),
      1
    );
  },

  async handleStep({ lineUserId, step, state, message }) {
    const value = textValue(message);

    if (step === 1) {
      const [departureCity, departureAirport] = parseAirport(value);
      return quickAsk('預設幣別？', currencyOptions, 2, { departureCity, departureAirport });
    }

    if (step === 2) {
      return quickAsk('預設同行人數？', travelerOptions, 3, { ...state, preferredCurrency: value });
    }

    if (step === 3) {
      return quickAsk('語言偏好？', languageOptions, 4, { ...state, defaultTravelerCount: parseCount(value, 1) });
    }

    const saved = await updateUserSettings(lineUserId, {
      departureCity: state.departureCity,
      departureAirport: state.departureAirport,
      preferredCurrency: state.preferredCurrency?.toUpperCase(),
      defaultTravelerCount: state.defaultTravelerCount,
      language: normalizeLanguage(value)
    });

    return done({
      type: 'text',
      text: [
        '設定已儲存。',
        `出發地：${saved.departure_city} (${saved.departure_airport})`,
        `幣別：${saved.preferred_currency}`,
        `預設人數：${saved.default_traveler_count}`,
        `語言：${saved.language}`,
        '',
        '之後「說走就走」和機票功能會優先使用這些設定。'
      ].join('\n')
    });
  }
};

function parseAirport(value) {
  if (value.includes('|')) return value.split('|');
  const code = value.toUpperCase();
  const airport = taiwanAirports.find((item) => item.value === code) ?? taiwanAirports[0];
  return [airport.city, airport.value];
}

function normalizeLanguage(value) {
  if (String(value).includes('English')) return 'en';
  if (String(value).includes('日本')) return 'ja';
  return 'zh-TW';
}
