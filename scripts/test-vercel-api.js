import webhook from '../api/webhook.js';
import ready from '../api/ready.js';
import fareRefresh from '../api/fare-refresh.js';
import priceCheck from '../api/price-check.js';

await expectHandler('ready', ready, mockReq('GET', {}));
await expectHandler('webhook', webhook, mockReq('POST', {
  events: [{
    type: 'message',
    replyToken: 'vercel-test-reply',
    source: { type: 'user', userId: 'vercel-test-user' },
    message: { id: crypto.randomUUID(), type: 'text', text: 'M3' }
  }]
}));
await expectHandler('fare-refresh', fareRefresh, mockReq('GET', {}));
await expectHandler('price-check', priceCheck, mockReq('GET', {}));

console.log('vercel-api test ok');

async function expectHandler(name, handler, req) {
  const res = mockRes();
  await handler(req, res);
  if (res.statusCode < 200 || res.statusCode >= 300) {
    throw new Error(`${name} returned ${res.statusCode}: ${res.body}`);
  }
  const data = JSON.parse(res.body);
  if (!data.ok) throw new Error(`${name} returned ok=false: ${res.body}`);
}

function mockReq(method, body) {
  return {
    method,
    headers: {},
    body
  };
}

function mockRes() {
  return {
    statusCode: 200,
    headers: {},
    body: '',
    setHeader(key, value) {
      this.headers[key.toLowerCase()] = value;
    },
    end(value = '') {
      this.body = String(value);
    }
  };
}
