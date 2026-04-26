import { createItinerary } from '../repositories/itineraryRepository.js';
import { getUser } from '../repositories/userRepository.js';
import { normalizeModuleInput } from '../services/llmInputNormalizer.js';
import { generateTravelPlan } from '../services/openai.js';
import { showLoadingAnimation } from '../services/line.js';
import { planCard } from '../views/flex/planCard.js';
import { askWithQuickReplies, cardAsk, dateAsk, done, parseCount, textValue } from './shared.js';
import { popularDestinations } from './options.js';

const travelerOptions = ['1人', '2人', '3人', '4人', '5人以上'];
const budgetOptions = ['精省：3萬內/人', '剛好：3-6萬/人', '舒服：6萬以上/人'];
const styleOptions = ['第一次去穩穩玩', '美食優先', '購物採買', '親子慢步調', '拍照景點', '追星/活動'];
const lodgingOptions = ['車站旁', '市中心商圈', '機場快線沿線', '海景/度假區', '便宜乾淨即可'];
const specialOptions = ['無', '親子同行', '長輩同行', '美食優先', '不想太累', '直飛優先'];

export const m2 = {
  async start() {
    return cardAsk(
      '完整出國規劃',
      '我會依序確認日期、人數、預算、玩法與住宿偏好，最後給你一份可直接拿去訂票訂房的計畫。',
      popularDestinations,
      1
    );
  },

  async handleStep({ lineUserId, step, state, message }) {
    const rawValue = textValue(message);

    // step 1: destination → ask traveler count
    if (step === 1) {
      return askWithQuickReplies('這次幾個人出發？', travelerOptions, 2, { destination: rawValue });
    }

    // step 2: traveler count → ask departure date
    if (step === 2) {
      return dateAsk('預計哪一天出發？', 3, { ...state, travelerCount: parseCount(rawValue, 1) });
    }

    // step 3: departure date → ask return date
    if (step === 3) {
      const startDate = await normalizeDate(rawValue, 'startDate', state);
      if (!startDate) return dateAsk('日期格式不對，請重新選出發日。', 3, state);
      return dateAsk('預計哪一天回來？', 4, { ...state, startDate });
    }

    // step 4: return date → ask budget
    if (step === 4) {
      const endDate = await normalizeDate(rawValue, 'endDate', state);
      if (!endDate) return dateAsk('日期格式不對，請重新選回程日。', 4, state);
      if (new Date(endDate) < new Date(state.startDate)) {
        return dateAsk('回程日不能早於出發日，請重新選。', 4, state);
      }
      return askWithQuickReplies('預算大概抓多少？', budgetOptions, 5, { ...state, endDate });
    }

    // step 5: budget → ask style
    if (step === 5) {
      return askWithQuickReplies('這趟旅行比較想要哪種節奏？', styleOptions, 6, { ...state, budgetLevel: rawValue });
    }

    // step 6: style → ask lodging
    if (step === 6) {
      return askWithQuickReplies('住宿想優先放在哪裡？', lodgingOptions, 7, { ...state, style: rawValue });
    }

    // step 7: lodging → ask special needs
    if (step === 7) {
      return askWithQuickReplies(
        '有特殊需求或必去景點嗎？可直接輸入（例如：必去清水寺、長輩同行）。沒有就選「無」。',
        specialOptions,
        8,
        { ...state, lodgingPreference: rawValue }
      );
    }

    // step 8: build plan
    await showLoadingAnimation(lineUserId);
    const user = await getUser(lineUserId);
    const input = {
      ...state,
      specialNeeds: rawValue === '無' ? '' : rawValue,
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
    }).catch((error) => {
      console.error('Failed to save full itinerary', error);
    });
    return done(planCard(plan, input));
  }
};

async function normalizeDate(rawValue, field, state) {
  const value = await normalizeModuleInput({
    moduleId: 'M2',
    field,
    rawValue,
    state
  });
  return isIsoDate(value) ? value : null;
}

function isIsoDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

function budgetToTwd(level = '') {
  if (level.includes('3萬內')) return 30000;
  if (level.includes('6萬以上')) return 70000;
  return 50000;
}
