import '../src/config/env.js';

if (!process.env.LINE_CHANNEL_ACCESS_TOKEN) {
  throw new Error('LINE_CHANNEL_ACCESS_TOKEN is required');
}

const endpoint = 'https://api.line.me/v2/bot';
const authHeaders = {
  authorization: `Bearer ${process.env.LINE_CHANNEL_ACCESS_TOKEN}`
};

const data = await lineFetch(`${endpoint}/richmenu/list`, {
  method: 'GET',
  headers: authHeaders
});

for (const menu of data.richmenus ?? []) {
  console.log([
    menu.richMenuId,
    menu.name,
    `${menu.size.width}x${menu.size.height}`,
    menu.chatBarText
  ].join(' | '));
}

async function lineFetch(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`LINE API ${response.status}: ${body}`);
  }
  const text = await response.text();
  return text ? JSON.parse(text) : {};
}
