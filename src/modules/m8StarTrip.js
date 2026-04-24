import { createItinerary } from '../repositories/itineraryRepository.js';
import { generateTravelPlan } from '../services/openai.js';
import { searchStarEvents } from '../services/starEvents.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, done, quickAsk, textValue } from './shared.js';

export const m8 = {
  async start() {
    return ask('\u8acb\u8f38\u5165\u85dd\u4eba\u6216\u5076\u50cf\u540d\u7a31\u3002', 1);
  },

  async handleStep({ lineUserId, step, state, message }) {
    const value = textValue(message);
    if (step === 1) return quickAsk('\u6d3b\u52d5\u985e\u578b\uff1f', ['\u6f14\u5531\u6703', '\u898b\u9762\u6703', 'Showcase'], 2, { artistName: value });

    const eventSearch = await searchStarEvents(state.artistName, value);
    const input = { ...state, eventType: value, destination: '\u9996\u723e', eventSearch };
    const plan = await generateTravelPlan('star_trip', input);
    await createItinerary(lineUserId, {
      module: 'M8',
      destination: plan.destination ?? input.destination,
      content: plan
    });
    return done(planCard(plan, input));
  }
};
