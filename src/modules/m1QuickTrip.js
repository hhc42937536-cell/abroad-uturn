import { m1Text, zh } from '../constants/text.js';
import { createItinerary } from '../repositories/itineraryRepository.js';
import { getUser } from '../repositories/userRepository.js';
import { generateTravelPlan } from '../services/openai.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, done, quickAsk, textValue } from './shared.js';

export const m1 = {
  async start() {
    return quickAsk(m1Text.askRegion, m1Text.regions, 1);
  },

  async handleStep({ lineUserId, step, state, message }) {
    const value = textValue(message);
    if (step === 1) return quickAsk(m1Text.askDays, m1Text.dayOptions, 2, { ...state, region: value });
    if (step === 2) return ask(m1Text.askMustVisit, 3, { ...state, days: value });

    const user = await getUser(lineUserId);
    const input = {
      ...state,
      mustVisit: value === zh.skip ? '' : value,
      from: user?.departure_airport ?? 'TPE'
    };
    const plan = await generateTravelPlan('quick', input);
    await createItinerary(lineUserId, {
      module: 'M1',
      destination: plan.destination,
      travelerCount: user?.default_traveler_count ?? 1,
      content: plan
    });
    return done(planCard(plan, input));
  }
};
