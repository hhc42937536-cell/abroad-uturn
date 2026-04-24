import '../src/config/env.js';

const richMenuId = process.argv[2];

if (!process.env.LINE_CHANNEL_ACCESS_TOKEN) {
  throw new Error('LINE_CHANNEL_ACCESS_TOKEN is required');
}

if (!richMenuId) {
  throw new Error('Usage: node scripts/delete-rich-menu.js <richMenuId>');
}

const endpoint = 'https://api.line.me/v2/bot';
const authHeaders = {
  authorization: `Bearer ${process.env.LINE_CHANNEL_ACCESS_TOKEN}`
};

await lineFetch(`${endpoint}/richmenu/${richMenuId}`, {
  method: 'DELETE',
  headers: authHeaders
});

console.log(`Deleted rich menu: ${richMenuId}`);

async function lineFetch(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`LINE API ${response.status}: ${body}`);
  }
  return {};
}
