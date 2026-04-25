import { env } from '../config/env.js';
import { setCachedJson } from './apiCache.js';
import { M7_AUTO_CACHE_KEY } from './trendFeed.js';

const cityNewsQueries = {
  東京: ['東京 新景點 旅遊', '東京 必買 伴手禮 小家電'],
  大阪: ['大阪 新景點 旅遊', '大阪 必買 伴手禮 購物'],
  首爾: ['首爾 新景點 聖水洞', '首爾 醫美 韓式大頭照'],
  曼谷: ['曼谷 新景點 One Bangkok', '曼谷 必買 伴手禮 購物'],
  香港: ['香港 新景點 西九 啟德', '香港 必買 伴手禮'],
  新加坡: ['新加坡 新景點 Sentosa Sensoryscape', '新加坡 必買 伴手禮'],
  福岡: ['福岡 新景點 旅遊', '福岡 必買 伴手禮'],
  沖繩: ['沖繩 新景點 JUNGLIA', '沖繩 必買 伴手禮'],
  吉隆坡: ['吉隆坡 新景點 TRX', '吉隆坡 必買 伴手禮'],
  胡志明市: ['胡志明市 新景點 捷運', '胡志明市 必買 伴手禮'],
  馬尼拉: ['馬尼拉 新景點 BGC', '馬尼拉 必買 伴手禮']
};

const buyKeywords = ['必買', '伴手禮', '購物', '藥妝', '零食', '咖啡', '美妝', '小家電', '百貨', 'outlet'];
const spotKeywords = ['新景點', '開幕', '園區', '樂園', '展覽', '商場', 'museum', 'park', '主題', '地標'];
const planKeywords = ['行程', '攻略', '一日遊', '自由行', '路線', '夜市', '咖啡', '玩法', '景點'];

export async function refreshM7AutoFeed(defaultProfiles) {
  const cityEntries = Object.entries(defaultProfiles);
  const refreshedEntries = await Promise.all(
    cityEntries.map(async ([city, base]) => [city, await refreshCityProfile(city, base)])
  );

  const cities = Object.fromEntries(refreshedEntries);
  const feed = {
    updatedAt: todayIso(),
    source: 'google-news-rss',
    cities
  };

  await setCachedJson(M7_AUTO_CACHE_KEY, feed, env.M7_TREND_CACHE_SECONDS);
  return feed;
}

async function refreshCityProfile(city, base) {
  const queries = cityNewsQueries[city] ?? [`${city} 新景點`, `${city} 必買`];
  const batches = await Promise.all(queries.map((query) => fetchNewsTitles(query)));
  const titles = uniq(batches.flat()).slice(0, env.M7_AUTO_HEADLINES_LIMIT);

  const autoBuys = pickByKeywords(titles, buyKeywords, 2).map((title) => `新聞熱點：${title}`);
  const autoSpots = pickByKeywords(titles, spotKeywords, 3).map((title) => `近期焦點：${title}`);
  const autoPlans = pickByKeywords(titles, planKeywords, 2).map((title) => `跟風玩法：${title}`);

  return {
    ...base,
    updated: todayIso(),
    hotBuys: mergeList(autoBuys, base.hotBuys, 3),
    hotSpots: mergeList(autoSpots, base.hotSpots, 3),
    hotPlans: mergeList(autoPlans, base.hotPlans, 3),
    caution: mergeList([
      `本頁依近期公開新聞自動更新（${todayIso()}），熱門變化快請再確認營業/預約資訊。`
    ], base.caution, 3)
  };
}

async function fetchNewsTitles(query) {
  const url = googleNewsRssUrl(query);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);

  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) return [];
    const xml = await response.text();
    return parseRssTitles(xml);
  } catch {
    return [];
  } finally {
    clearTimeout(timeout);
  }
}

function googleNewsRssUrl(query) {
  const url = new URL('https://news.google.com/rss/search');
  url.searchParams.set('q', query);
  url.searchParams.set('hl', 'zh-TW');
  url.searchParams.set('gl', 'TW');
  url.searchParams.set('ceid', 'TW:zh-Hant');
  return url.toString();
}

function parseRssTitles(xml) {
  const blocks = xml.match(/<item>[\s\S]*?<\/item>/g) ?? [];
  return blocks
    .map((block) => {
      const matched = block.match(/<title>([\s\S]*?)<\/title>/);
      if (!matched) return '';
      return cleanTitle(matched[1]);
    })
    .filter(Boolean)
    .slice(0, 12);
}

function cleanTitle(value) {
  const raw = decodeXml(String(value || ''))
    .replace('<![CDATA[', '')
    .replace(']]>', '')
    .trim();
  if (!raw) return '';
  const noSource = raw.replace(/\s*[-|｜]\s*[^-|｜]{1,24}$/, '').trim();
  return clipText(noSource, 42);
}

function decodeXml(text) {
  return text
    .replaceAll('&amp;', '&')
    .replaceAll('&quot;', '"')
    .replaceAll('&#39;', "'")
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>');
}

function pickByKeywords(titles, keywords, limit) {
  const matched = titles.filter((title) => keywords.some((keyword) => title.toLowerCase().includes(keyword.toLowerCase())));
  return uniq(matched).slice(0, limit);
}

function mergeList(primary, fallback, limit) {
  return uniq([...(primary || []), ...(fallback || [])]).slice(0, limit);
}

function uniq(items) {
  return [...new Set((items || []).filter(Boolean))];
}

function clipText(text, maxLength) {
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}…` : text;
}

function todayIso() {
  const now = new Date();
  const y = now.getUTCFullYear();
  const m = String(now.getUTCMonth() + 1).padStart(2, '0');
  const d = String(now.getUTCDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}
