import '../src/config/env.js';

const baseUrl = process.env.APP_BASE_URL ?? 'http://localhost:3000';
const replyToken = 'dev-reply-token';
const userId = `dev-user-${Date.now()}`;

const scenarios = {
  menu: [text('\u9078\u55ae')],
  m1: [
    text('M1'),
    text('\u6771\u4e9e'),
    text('3\u5929'),
    text('\u7565\u904e')
  ],
  m2: [
    text('M2'),
    text('\u9996\u723e'),
    text('2026-05-20'),
    text('2026-05-24'),
    text('2'),
    text('\u4e2d 3~6\u842c'),
    text('\u7f8e\u98df'),
    text('\u7121')
  ],
  m3: [
    text('M3'),
    text('TPE')
  ],
  m9: [
    text('M9'),
    text('\u53f0\u5317'),
    text('TPE'),
    text('TWD'),
    text('2'),
    text('\u7e41\u4e2d')
  ]
};

const selected = process.argv[2] ?? 'm9';
const events = scenarios[selected];

if (!events) {
  throw new Error(`Unknown scenario "${selected}". Use one of: ${Object.keys(scenarios).join(', ')}`);
}

for (const event of events) {
  const response = await fetch(`${baseUrl}/webhook`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ events: [event] })
  });
  console.log(`${selected} ${event.type}: ${response.status}`);
}

function text(value) {
  return {
    type: 'message',
    replyToken,
    source: { type: 'user', userId },
    message: { id: crypto.randomUUID(), type: 'text', text: value }
  };
}
