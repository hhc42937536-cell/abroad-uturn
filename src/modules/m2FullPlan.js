import { m2Text, zh } from '../constants/text.js';
import { createItinerary } from '../repositories/itineraryRepository.js';
import { getUser } from '../repositories/userRepository.js';
import { normalizeModuleInput } from '../services/llmInputNormalizer.js';
import { generateTravelPlan } from '../services/openai.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, dateAsk, done, parseCount, quickAsk, textValue } from './shared.js';

const questions = {
  1: m2Text.destination,
  2: m2Text.startDate,
  3: m2Text.endDate,
  4: m2Text.travelerCount,
  5: m2Text.budget,
  6: m2Text.style,
  7: m2Text.specialNeeds
};

export const m2 = {
  async start() {
    return ask(questions[1], 1);
  },

  async handleStep({ lineUserId, step, state, message }) {
    const keys = ['destination', 'startDate', 'endDate', 'travelerCount', 'budgetLevel', 'style', 'specialNeeds'];
    const field = keys[step - 1];
    const value = await normalizeModuleInput({
      moduleId: 'M2',
      step,
      field,
      rawValue: textValue(message),
      state
    });

    if ((step === 2 || step === 3) && !isIsoDate(value)) {
      return ask(zh.invalidDate, step, state);
    }

    const nextState = { ...state, [keys[step - 1]]: value };

    if (step === 3 && new Date(nextState.endDate) < new Date(nextState.startDate)) {
      return dateAsk(zh.invalidEndDate, 3, state);
    }

    if (step === 1 || step === 2) return dateAsk(questions[step + 1], step + 1, nextState);
    if (step === 3) return quickAsk(questions[step + 1], ['1', '2', '3', '4', '4+'], step + 1, nextState);
    if (step === 4) return quickAsk(questions[step + 1], m2Text.budgetOptions, step + 1, nextState);
    if (step === 5) return quickAsk(questions[step + 1], m2Text.styleOptions, step + 1, nextState);
    if (step < 7) return ask(questions[step + 1], step + 1, nextState);

    const user = await getUser(lineUserId);
    const input = {
      ...nextState,
      travelerCount: parseCount(nextState.travelerCount, user?.default_traveler_count ?? 1),
      from: user?.departure_airport ?? 'TPE'
    };
    const plan = await generateTravelPlan('full', input);
    await createItinerary(lineUserId, {
      module: 'M2',
      destination: input.destination,
      startDate: input.startDate,
      endDate: input.endDate,
      travelerCount: input.travelerCount,
      budgetTwd: budgetToTwd(input.budgetLevel),
      content: plan
    });
    return done(planCard(plan, input));
  }
};

function isIsoDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function budgetToTwd(level) {
  if (String(level).includes('\u4f4e')) return 30000;
  if (String(level).includes('\u9ad8')) return 60000;
  return 45000;
}
