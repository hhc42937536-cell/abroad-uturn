import { env } from '../config/env.js';

export function skyscannerLink({ from = 'TPE', to = '', departDate = '', returnDate = '' }) {
  const path = `${from}/${to || 'anywhere'}/${compactDate(departDate)}/${compactDate(returnDate)}`.replace(/\/+$/, '');
  const url = new URL(`https://www.skyscanner.com.tw/transport/flights/${path}/`);
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

export function agodaLink(city) {
  const url = new URL('https://www.agoda.com/zh-tw/search');
  url.searchParams.set('city', city);
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

export function bookingLink(city) {
  const url = new URL('https://www.booking.com/searchresults.zh-tw.html');
  url.searchParams.set('ss', city);
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

export function tripLink(city) {
  const url = new URL(`https://tw.trip.com/travel-guide/destination/${encodeURIComponent(city)}`);
  if (env.TP_MARKER) url.searchParams.set('utm_source', env.TP_MARKER);
  return url.toString();
}

function compactDate(value) {
  return value ? String(value).replaceAll('-', '') : '';
}
