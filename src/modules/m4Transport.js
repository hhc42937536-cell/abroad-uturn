import { generateTravelPlan } from '../services/openai.js';
import { ask, done, textValue } from './shared.js';

export const m4 = {
  async start() {
    return ask('\u8acb\u8f38\u5165\u76ee\u7684\u5730\u57ce\u5e02\u3002', 1);
  },

  async handleStep({ message }) {
    const city = textValue(message);
    const guide = await generateTravelPlan('local_transport', { destination: city });
    return done({ type: 'text', text: formatGuide(city, guide) });
  }
};

function formatGuide(city, guide) {
  return [
    `${city} \u7576\u5730\u4ea4\u901a\u653b\u7565`,
    guide.summary,
    ...(guide.reminders ?? []).map((item) => `- ${item}`)
  ].filter(Boolean).join('\n');
}
