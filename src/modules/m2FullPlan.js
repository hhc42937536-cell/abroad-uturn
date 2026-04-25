import { createItinerary } from '../repositories/itineraryRepository.js';
import { getUser } from '../repositories/userRepository.js';
import { normalizeModuleInput } from '../services/llmInputNormalizer.js';
import { generateTravelPlan } from '../services/openai.js';
import { planCard } from '../views/flex/planCard.js';
import { ask, askWithQuickReplies, cardAsk, dateAsk, done, parseCount, textValue } from './shared.js';
import { popularDestinations } from './options.js';

const travelerOptions = ['1人', '2人', '3人', '4人', '5人以上'];
const budgetOptions = ['精省：3萬內/人', '剛好：3-6萬/人', '舒服：6萬以上/人'];
const styleOptions = ['第一次去穩穩玩', '美食優先', '購物採買', '親子慢步調', '拍照景點', '追星/活動'];
const lodgingOptions = ['車站旁', '市中心商圈', '機場快線沿線', '海景/度假區', '便宜乾淨即可'];
const specialOptions = ['無', '必去景點', '指定機場', '指定班機時間', '長輩同行', '小孩同行', '不想太累'];

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

    if (step === 1) {
      return dateAsk('預計哪一天出發？', 2, { destination: rawValue });
    }

    if (step === 2) {
      const startDate = await normalizeDate(rawValue, step, state);
      if (!startDate) return dateAsk('日期格式不對，請重新選出發日。', 2, state);
      return dateAsk('預計哪一天回來？', 3, { ...state, startDate });
    }

    if (step === 3) {
      const endDate = await normalizeDate(rawValue, step, state);
      if (!endDate) return dateAsk('日期格式不對，請重新選回程日。', 3, state);
      if (new Date(endDate) < new Date(state.startDate)) {
        return dateAsk('回程日不能早於出發日，請重新選回程日。', 3, state);
      }
      return askWithQuickReplies('這次幾個人出發？', travelerOptions, 4, { ...state, endDate });
    }

    if (step === 4) {
      return askWithQuickReplies('預算大概抓多少？', budgetOptions, 5, { ...state, travelerCount: parseCount(rawValue, 1) });
    }

    if (step === 5) {
      return askWithQuickReplies('這趟旅行比較想要哪種節奏？', styleOptions, 6, { ...state, budgetLevel: rawValue });
    }

    if (step === 6) {
      return askWithQuickReplies('住宿想優先放在哪裡？', lodgingOptions, 7, { ...state, style: rawValue });
    }

    if (step === 7) {
      return askWithQuickReplies('有沒有必去景點、同行狀況或其他限制？', specialOptions, 8, { ...state, lodgingPreference: rawValue });
    }

    const user = await getUser(lineUserId);
    const input = {
      ...state,
      specialNeeds: rawValue === '無' ? '' : rawValue,
      mustVisit: rawValue === '無' ? '' : rawValue,
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

async function normalizeDate(rawValue, step, state) {
  const value = await normalizeModuleInput({
    moduleId: 'M2',
    step,
    field: step === 2 ? 'startDate' : 'endDate',
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
