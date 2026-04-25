import { createItinerary } from '../repositories/itineraryRepository.js';
import { generateTravelPlan } from '../services/openai.js';
import { searchStarEvents } from '../services/starEvents.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, cardAsk, done, quickAsk, textValue } from './shared.js';
import { popularArtists, popularDestinations } from './options.js';

const eventTypes = ['演唱會', '見面會', '音樂節', '頒獎典禮', '快閃活動'];
const dayOptions = ['2天', '3天', '4天', '5天'];

export const m8 = {
  async start() {
    return cardAsk(
      '追星行程規劃',
      '先選藝人或直接輸入名字，我會把場館、住宿區、交通和周邊行程一起排。',
      popularArtists,
      1
    );
  },

  async handleStep({ lineUserId, step, state, message }) {
    const value = textValue(message);

    if (step === 1) return quickAsk('是哪一種活動？', eventTypes, 2, { artistName: value });

    if (step === 2) {
      return cardAsk(
        '活動在哪個城市？',
        '如果還不知道城市，先選最可能的目的地，之後可再調整。',
        popularDestinations.slice(0, 11),
        3,
        { ...state, eventType: value }
      );
    }

    if (step === 3) return quickAsk('這趟追星行程排幾天？', dayOptions, 4, { ...state, destination: value });

    if (step === 4) {
      return ask('有沒有指定場館、搶票時間、必去店家或同行狀況？沒有請回「無」。', 5, { ...state, days: value });
    }

    const eventSearch = await searchStarEvents(state.artistName, state.eventType);
    const input = {
      ...state,
      mustVisit: value === '無' ? `${state.eventType} 場館` : value,
      eventSearch
    };
    const plan = await generateTravelPlan('star_trip', input);
    await createItinerary(lineUserId, {
      module: 'M8',
      destination: plan.destination ?? input.destination,
      content: { ...plan, eventSearch }
    }).catch((error) => {
      console.error('Failed to save star trip itinerary', error);
    });
    return done(planCard(plan, input));
  }
};
