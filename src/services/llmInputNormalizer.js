import { env } from '../config/env.js';
import { completeJson } from './openai.js';

export async function normalizeModuleInput({ moduleId, step, field, rawValue, state }) {
  const deterministic = normalizeDeterministic(field, rawValue);
  if (deterministic.changed || !env.LLM_INPUT_NORMALIZATION) return deterministic.value;

  const normalized = await completeJson({
    system: [
      'You normalize LINE bot user input for a travel planning state machine.',
      'Return JSON only with shape {"value": string, "confidence": number}.',
      'Do not add new facts. Only correct obvious typos or convert formats.',
      'For dates, prefer YYYY-MM-DD. If uncertain, keep the original value.'
    ].join(' '),
    user: {
      moduleId,
      step,
      field,
      rawValue,
      state,
      today: new Date().toISOString().slice(0, 10),
      locale: 'zh-TW'
    },
    temperature: 0
  });

  if (!normalized || typeof normalized.value !== 'string') return rawValue;
  if (Number(normalized.confidence ?? 0) < 0.75) return rawValue;
  return normalized.value.trim();
}

function normalizeDeterministic(field, rawValue) {
  const value = String(rawValue ?? '').trim();

  if (field === 'startDate' || field === 'endDate') {
    const date = normalizeDate(value);
    if (date) return { value: date, changed: date !== value };
  }

  if (field === 'travelerCount') {
    const count = value.match(/\d+/)?.[0];
    if (count) return { value: count, changed: count !== value };
  }

  if (field === 'budgetLevel') {
    if (/[低省便宜]/.test(value) || value.includes('<3')) return { value: '\u4f4e <3\u842c', changed: true };
    if (/[高豪]/.test(value) || value.includes('>6')) return { value: '\u9ad8 >6\u842c', changed: true };
    if (/[中普]/.test(value) || value.includes('3') || value.includes('6')) return { value: '\u4e2d 3~6\u842c', changed: true };
  }

  if (field === 'style') {
    const styles = [
      ['\u81ea\u7136', /自然|山|海|戶外/],
      ['\u6587\u5316', /文化|歷史|博物館|寺/],
      ['\u7f8e\u98df', /美食|吃|餐|咖啡/],
      ['\u8cfc\u7269', /購物|買|逛街|Outlet/i],
      ['\u6df7\u5408', /混合|都可|隨意|全部/]
    ];
    const matched = styles.find(([, pattern]) => pattern.test(value));
    if (matched) return { value: matched[0], changed: matched[0] !== value };
  }

  return { value, changed: false };
}

function normalizeDate(value) {
  const matched = value.match(/^(\d{4})[\/\-.](\d{1,2})[\/\-.](\d{1,2})$/);
  if (!matched) return null;

  const [, year, month, day] = matched;
  const normalized = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  const date = new Date(`${normalized}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return null;
  if (date.toISOString().slice(0, 10) !== normalized) return null;
  return normalized;
}
