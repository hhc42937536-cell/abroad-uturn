import { env } from '../config/env.js';

const destinationAirportMap = {
  東京: 'NRT',
  大阪: 'KIX',
  京都: 'KIX',
  首爾: 'ICN',
  釜山: 'PUS',
  濟州島: 'CJU',
  濟州: 'CJU',
  曼谷: 'BKK',
  香港: 'HKG',
  澳門: 'MFM',
  新加坡: 'SIN',
  福岡: 'FUK',
  沖繩: 'OKA',
  那霸: 'OKA',
  吉隆坡: 'KUL',
  胡志明: 'SGN',
  胡志明市: 'SGN',
  馬尼拉: 'MNL',
  峇里島: 'DPS',
  札幌: 'CTS',
  名古屋: 'NGO',
  清邁: 'CNX',
  普吉島: 'HKT',
  普吉: 'HKT',
  河內: 'HAN',
  峴港: 'DAD',
  富國島: 'PQC',
  芽莊: 'CXR',
  金邊: 'PNH',
  暹粒: 'SAI',
  永珍: 'VTE',
  琅勃拉邦: 'LPQ',
  檳城: 'PEN',
  沙巴: 'BKI',
  亞庇: 'BKI',
  蘭卡威: 'LGK',
  宿霧: 'CEB',
  長灘島: 'MPH',
  雅加達: 'CGK',
  上海: 'PVG',
  北京: 'PEK',
  廣州: 'CAN',
  深圳: 'SZX',
  杭州: 'HGH',
  廈門: 'XMN',
  洛杉磯: 'LAX',
  紐約: 'JFK',
  舊金山: 'SFO',
  西雅圖: 'SEA',
  夏威夷: 'HNL',
  檀香山: 'HNL',
  關島: 'GUM',
  倫敦: 'LHR',
  巴黎: 'CDG'
};

export function skyscannerLink({ from = 'TPE', to = '', destination = '', departDate = '', returnDate = '' } = {}) {
  const origin = normalizeAirportCode(from, 'TPE');
  const target = normalizeAirportCode(to || destinationAirportCode(destination), 'everywhere');
  const segments = [origin, target, compactDate(departDate), compactDate(returnDate)].filter(Boolean);
  const url = new URL(`https://www.skyscanner.com.tw/transport/flights/${segments.join('/')}/`);
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

export function destinationAirportCode(destination = '') {
  const normalized = String(destination).trim();
  if (/^[A-Za-z]{3}$/.test(normalized)) return normalized.toUpperCase();
  return destinationAirportMap[normalized] ?? '';
}

export function agodaLink(city, keyword = '') {
  const url = new URL('https://www.agoda.com/zh-tw/search');
  url.searchParams.set('textToSearch', [city, keyword].filter(Boolean).join(' '));
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

export function bookingLink(city, keyword = '') {
  const url = new URL('https://www.booking.com/searchresults.zh-tw.html');
  url.searchParams.set('ss', [city, keyword].filter(Boolean).join(' '));
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

export function googleMapsSearchLink(query) {
  const url = new URL('https://www.google.com/maps/search/');
  url.searchParams.set('api', '1');
  url.searchParams.set('query', String(query || '').trim());
  url.searchParams.set('hl', 'zh-TW');
  return url.toString();
}

export function googleMapsDirectionsLink({ origin = '', destination = '', travelmode = 'transit' } = {}) {
  const url = new URL('https://www.google.com/maps/dir/');
  url.searchParams.set('api', '1');
  if (origin) url.searchParams.set('origin', origin);
  if (destination) url.searchParams.set('destination', destination);
  if (travelmode) url.searchParams.set('travelmode', travelmode);
  url.searchParams.set('hl', 'zh-TW');
  return url.toString();
}

export function googleSearchLink(query) {
  const url = new URL('https://www.google.com/search');
  url.searchParams.set('q', String(query || '').trim());
  url.searchParams.set('hl', 'zh-TW');
  return url.toString();
}

export function tripLink(city) {
  const url = new URL(`https://tw.trip.com/travel-guide/destination/${encodeURIComponent(city)}`);
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

function normalizeAirportCode(value, fallback) {
  const code = String(value || '').trim();
  if (code === 'everywhere') return code;
  return /^[A-Za-z]{3}$/.test(code) ? code.toLowerCase() : fallback;
}

function compactDate(value) {
  return value ? String(value).replaceAll('-', '') : '';
}
