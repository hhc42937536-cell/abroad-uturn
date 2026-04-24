import { m9Text, zh } from '../constants/text.js';
import { updateUserSettings } from '../repositories/userRepository.js';
import { ask, done, parseCount, quickAsk, textValue } from './shared.js';

const prompts = {
  1: m9Text.departureCity,
  2: m9Text.departureAirport,
  3: m9Text.currency,
  4: m9Text.travelerCount,
  5: m9Text.language
};

export const m9 = {
  async start() {
    return ask(prompts[1], 1);
  },

  async handleStep({ lineUserId, step, state, message }) {
    const value = textValue(message);
    const keys = ['departureCity', 'departureAirport', 'preferredCurrency', 'defaultTravelerCount', 'language'];
    const nextState = { ...state, [keys[step - 1]]: value };

    if (step === 3) return quickAsk(prompts[step + 1], ['1', '2', '3', '4'], step + 1, nextState);
    if (step === 4) return quickAsk(prompts[step + 1], [zh.traditionalChinese, zh.english, zh.japanese], step + 1, nextState);
    if (step < 5) return ask(prompts[step + 1], step + 1, nextState);

    const saved = await updateUserSettings(lineUserId, {
      departureCity: nextState.departureCity,
      departureAirport: nextState.departureAirport?.toUpperCase(),
      preferredCurrency: nextState.preferredCurrency?.toUpperCase(),
      defaultTravelerCount: parseCount(nextState.defaultTravelerCount),
      language: normalizeLanguage(nextState.language)
    });

    return done({
      type: 'text',
      text: [
        m9Text.savedSettings ?? zh.savedSettings,
        `${m9Text.departure}\uff1a${saved.departure_city} (${saved.departure_airport})`,
        `${m9Text.currencyLabel}\uff1a${saved.preferred_currency}`,
        `${m9Text.travelers}\uff1a${saved.default_traveler_count}`,
        `${m9Text.languageLabel}\uff1a${saved.language}`
      ].join('\n')
    });
  }
};

function normalizeLanguage(value) {
  if (String(value).includes('\u82f1')) return 'en';
  if (String(value).includes('\u65e5')) return 'ja';
  return 'zh-TW';
}
