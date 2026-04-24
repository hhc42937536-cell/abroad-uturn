import { env } from '../config/env.js';

export async function completeJson({ system, user, temperature = 0.2 }) {
  if (!env.OPENAI_API_KEY) return null;

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.OPENAI_API_KEY}`,
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      model: env.OPENAI_MODEL,
      response_format: { type: 'json_object' },
      temperature,
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: JSON.stringify(user) }
      ]
    })
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`OpenAI request failed ${response.status}: ${body}`);
  }

  const data = await response.json();
  return JSON.parse(data.choices[0].message.content);
}

export async function generateTravelPlan(kind, input) {
  const generated = await completeJson({
    system: [
      'You are a travel planning assistant for Taiwanese travelers.',
      'Return JSON only.',
      'Use Traditional Chinese for user-facing text.',
      'Be practical and do not invent live prices or live availability.'
    ].join(' '),
    user: { kind, input },
    temperature: 0.4
  }).catch((error) => {
    console.error('OpenAI travel plan failed', error);
    return null;
  });

  return generated ?? fallbackPlan(kind, input);
}

function fallbackPlan(kind, input) {
  const destination = input.destination ?? input.region ?? '\u9996\u723e';
  return {
    title: kind === 'quick' ? '\u8aaa\u8d70\u5c31\u8d70\u63a8\u85a6' : '\u5b8c\u6574\u51fa\u570b\u8a08\u756b',
    destination,
    summary: `${destination} \u9069\u5408\u4ee5\u4ea4\u901a\u4fbf\u5229\u3001\u9910\u98f2\u9078\u64c7\u591a\u7684\u5340\u57df\u4f5c\u70ba\u4f4f\u5bbf\u64da\u9ede\u3002`,
    flights: [
      { label: '\u6bd4\u50f9\u641c\u5c0b', note: '\u958b\u555f Skyscanner \u67e5\u770b\u6700\u65b0\u822a\u73ed\u8207\u7968\u50f9\u3002' }
    ],
    hotels: [
      { name: `${destination} \u5e02\u4e2d\u5fc3\u4f4f\u5bbf`, note: '\u512a\u5148\u9078\u64c7\u8eca\u7ad9\u6216\u4e3b\u8981\u5546\u5708\u5468\u908a\u3002' }
    ],
    days: [
      { day: 1, morning: '\u62b5\u9054\u8207\u4ea4\u901a\u5361\u8a2d\u5b9a', afternoon: '\u5e02\u4e2d\u5fc3\u6563\u7b56', evening: '\u5728\u5730\u7f8e\u98df' },
      { day: 2, morning: '\u7d93\u5178\u666f\u9ede', afternoon: '\u5496\u5561\u8207\u8cfc\u7269', evening: '\u591c\u666f\u6216\u591c\u5e02' }
    ],
    reminders: ['\u78ba\u8a8d\u8b77\u7167\u6548\u671f', '\u51fa\u767c\u524d\u518d\u6b21\u78ba\u8a8d\u7c3d\u8b49\u8207\u5165\u5883\u898f\u5b9a']
  };
}
