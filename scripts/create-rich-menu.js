import '../src/config/env.js';
import { access, readFile } from 'node:fs/promises';
import { dirname, extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

if (!process.env.LINE_CHANNEL_ACCESS_TOKEN) {
  throw new Error('LINE_CHANNEL_ACCESS_TOKEN is required');
}

const endpoint = 'https://api.line.me/v2/bot';
const uploadEndpoint = 'https://api-data.line.me/v2/bot';
const __dirname = dirname(fileURLToPath(import.meta.url));
const defaultImagePath = join(__dirname, '..', 'assets', 'rich-menu.png');
const imagePath = process.env.RICH_MENU_IMAGE_PATH || await existingPath(defaultImagePath);
const authHeaders = {
  authorization: `Bearer ${process.env.LINE_CHANNEL_ACCESS_TOKEN}`
};

const richMenu = {
  size: { width: 2500, height: 1686 },
  selected: true,
  name: 'travel-main-menu',
  chatBarText: '\u2728 \u9ede\u6211\u958b\u59cb\u898f\u5283\u65c5\u7a0b \u25be',
  areas: [
    area(0, 0, 833, 562, 'M1'),
    area(833, 0, 834, 562, 'M2'),
    area(1667, 0, 833, 562, 'M3'),
    area(0, 562, 833, 562, 'M4'),
    area(833, 562, 834, 562, 'M5'),
    area(1667, 562, 833, 562, 'M6'),
    area(0, 1124, 833, 562, 'M7'),
    area(833, 1124, 834, 562, 'M8'),
    area(1667, 1124, 833, 562, 'M9')
  ]
};

const created = await lineFetch(`${endpoint}/richmenu`, {
  method: 'POST',
  headers: { ...authHeaders, 'content-type': 'application/json' },
  body: JSON.stringify(richMenu)
});

if (imagePath) {
  const image = await readFile(imagePath);
  await lineFetch(`${uploadEndpoint}/richmenu/${created.richMenuId}/content`, {
    method: 'POST',
    headers: {
      ...authHeaders,
      'content-type': contentType(imagePath)
    },
    body: image
  });
}

await lineFetch(`${endpoint}/user/all/richmenu/${created.richMenuId}`, {
  method: 'POST',
  headers: authHeaders
});

console.log(`Created default rich menu: ${created.richMenuId}`);
if (!imagePath) {
  console.log('No rich menu image found. Set RICH_MENU_IMAGE_PATH or run npm run asset:rich-menu.');
}

function area(x, y, width, height, id) {
  return {
    bounds: { x, y, width, height },
    action: {
      type: 'postback',
      data: `action=module&id=${id}`,
      displayText: id
    }
  };
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

function contentType(path) {
  const ext = extname(path).toLowerCase();
  if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
  if (ext === '.png') return 'image/png';
  throw new Error('RICH_MENU_IMAGE_PATH must be a .png, .jpg, or .jpeg file');
}

async function existingPath(path) {
  try {
    await access(path);
    return path;
  } catch {
    return '';
  }
}
