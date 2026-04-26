/**
 * Formats a saved itinerary record into a shareable plain-text travel plan document.
 * LINE text messages support up to 5000 characters.
 */
export function formatPlanDocument(itinerary) {
  const c = itinerary.content ?? {};
  const destination = itinerary.destination ?? c.destination ?? '目的地';
  const days = Array.isArray(c.days) ? c.days : [];
  const budget = c.budget ?? null;
  const reminders = Array.isArray(c.reminders) ? c.reminders : [];
  const flightPicks = c.flightPicks ?? null;
  const hotelPicks = c.hotelPicks ?? null;

  const lines = [];

  // ── Header ──────────────────────────────────
  lines.push(`📋 ${c.title ?? `${destination} 行程計畫書`}`);
  lines.push('');

  // ── Basic info ──────────────────────────────
  lines.push(`🌏 目的地：${destination}`);

  const travelers = itinerary.traveler_count ?? itinerary.travelerCount;
  if (travelers) lines.push(`👥 人數：${travelers} 人`);

  const startDate = itinerary.start_date ?? itinerary.startDate;
  const endDate = itinerary.end_date ?? itinerary.endDate;
  if (startDate && endDate) {
    lines.push(`📅 日期：${startDate} ～ ${endDate}`);
  } else if (days.length) {
    lines.push(`📅 天數：${days.length} 天`);
  }

  // ── Flight (M1 quickDecision) ────────────────
  const cheapest = flightPicks?.cheapest;
  if (cheapest) {
    const route = cheapest.route ? `${cheapest.route}  ` : '';
    const price = cheapest.priceText ? `${cheapest.priceText}  ` : '';
    const date = cheapest.departDate ? `出發 ${cheapest.departDate}` : '近7天內';
    lines.push(`✈️ 推薦機票：${route}${price}${date}`);
  }

  // ── Hotel (M1 quickDecision) ─────────────────
  const bestHotel = hotelPicks?.best;
  if (bestHotel?.title) {
    lines.push(`🏨 推薦住宿：${bestHotel.title}`);
    if (bestHotel.reason) lines.push(`   ${bestHotel.reason}`);
  }

  // ── Summary ──────────────────────────────────
  if (c.summary) {
    lines.push('');
    lines.push(`💬 ${c.summary}`);
  }

  // ── Daily itinerary ──────────────────────────
  if (days.length) {
    lines.push('');
    lines.push('━━━━━━━━━━━━━━━━━━━━');
    lines.push('每日行程');
    lines.push('━━━━━━━━━━━━━━━━━━━━');
    days.forEach((day) => {
      lines.push('');
      lines.push(`▌ Day ${day.day}`);
      if (day.morning) lines.push(`  🌅 上午：${day.morning}`);
      if (day.afternoon) lines.push(`  ☀️ 下午：${day.afternoon}`);
      if (day.evening) lines.push(`  🌙 晚上：${day.evening}`);
    });
  }

  // ── Budget ───────────────────────────────────
  if (budget) {
    lines.push('');
    lines.push('━━━━━━━━━━━━━━━━━━━━');
    lines.push(`💰 ${budget.title ?? '預算參考'}：${budget.totalText ?? ''}`);
    lines.push('━━━━━━━━━━━━━━━━━━━━');
    if (Array.isArray(budget.lines)) {
      budget.lines.forEach((line) => lines.push(`  ${line}`));
    }
    if (budget.note) lines.push(`  ${budget.note}`);
  }

  // ── Reminders ────────────────────────────────
  if (reminders.length) {
    lines.push('');
    lines.push('━━━━━━━━━━━━━━━━━━━━');
    lines.push('📝 出發前提醒');
    lines.push('━━━━━━━━━━━━━━━━━━━━');
    reminders.forEach((r) => lines.push(`• ${r}`));
  }

  lines.push('');
  lines.push('⚠️ 本計畫書由 AI 生成，出發前請以訂購頁最終金額與官方資訊為準。');

  // Guard: truncate to LINE's 5000-char limit
  const text = lines.join('\n');
  return text.length > 4800 ? `${text.slice(0, 4797)}...` : text;
}
