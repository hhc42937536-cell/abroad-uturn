import '../src/config/env.js';

if (!process.env.LINE_CHANNEL_ACCESS_TOKEN) {
  throw new Error('LINE_CHANNEL_ACCESS_TOKEN is required');
}

if (!process.env.APP_BASE_URL) {
  throw new Error('APP_BASE_URL is required, for example https://your-service.onrender.com');
}

const endpointUrl = new URL('/webhook', process.env.APP_BASE_URL).toString();
const apiEndpoint = 'https://api.line.me/v2/bot/channel/webhook/endpoint';
const authHeaders = {
  authorization: `Bearer ${process.env.LINE_CHANNEL_ACCESS_TOKEN}`
};

await lineFetch(apiEndpoint, {
  method: 'PUT',
  headers: { ...authHeaders, 'content-type': 'application/json' },
  body: JSON.stringify({ endpoint: endpointUrl })
});

const current = await lineFetch(apiEndpoint, {
  method: 'GET',
  headers: authHeaders
});

console.log(`LINE webhook endpoint set to: ${current.endpoint}`);
console.log(`Active: ${current.active}`);

async function lineFetch(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`LINE API ${response.status}: ${body}`);
  }
  const text = await response.text();
  return text ? JSON.parse(text) : {};
}
