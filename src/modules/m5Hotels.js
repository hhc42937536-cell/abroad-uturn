import { agodaLink, bookingLink } from '../services/deepLinks.js';
import { ask, done, quickAsk, textValue } from './shared.js';

export const m5 = {
  async start() {
    return ask('\u8acb\u8f38\u5165\u57ce\u5e02\u3002', 1);
  },

  async handleStep({ step, state, message }) {
    const value = textValue(message);
    if (step === 1) return quickAsk('\u4f4f\u5bbf\u985e\u578b\uff1f', ['\u98ef\u5e97', '\u9752\u65c5', '\u6c11\u5bbf', '\u516c\u5bd3'], 2, { city: value });
    if (step === 2) return quickAsk('\u4f4f\u5bbf\u5340\u57df\uff1f', ['\u71b1\u9580\u89c0\u5149\u5340', '\u6a5f\u5834\u9644\u8fd1', '\u5546\u696d\u5340'], 3, { ...state, type: value });

    const city = state.city;
    return done({
      type: 'text',
      text: [
        `${city} ${state.type}\u4f4f\u5bbf\u63a8\u85a6\u65b9\u5411`,
        `\u5340\u57df\uff1a${value}`,
        '1. \u5e02\u4e2d\u5fc3\u4ea4\u901a\u6a1e\u7d10\uff1a\u9069\u5408\u9996\u6b21\u9020\u8a2a\u3002',
        '2. \u4e3b\u8981\u5546\u5708\u5468\u908a\uff1a\u9910\u98f2\u8207\u8cfc\u7269\u65b9\u4fbf\u3002',
        '3. \u6a5f\u5834\u5feb\u7dda\u6cbf\u7dda\uff1a\u9069\u5408\u65e9\u665a\u73ed\u6a5f\u3002',
        `Agoda: ${agodaLink(city)}`,
        `Booking: ${bookingLink(city)}`
      ].join('\n')
    });
  }
};
