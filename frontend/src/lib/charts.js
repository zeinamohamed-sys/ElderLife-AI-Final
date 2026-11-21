/** Pure helpers for the charts (no React, so they can be unit-tested with node --test). */
export const LEVELS = ["Normal", "Low", "Medium", "High", "Critical"];
export const levelIndex = (l) => Math.max(0, LEVELS.indexOf(l));

/** The API returns risk history newest first. Returns [[x, y], ...] oldest -> newest inside a w x h box (y grows downward, Critical at the top). */
export function trendPoints(history, w = 220, h = 48, pad = 4) {
  const pts = [...(history || [])].reverse();
  if (pts.length === 0) return [];
  const step = pts.length > 1 ? (w - 2 * pad) / (pts.length - 1) : 0;
  return pts.map((p, i) => [Math.round((pad + i * step) * 10) / 10, Math.round((h - pad - (levelIndex(p.level) / (LEVELS.length - 1)) * (h - 2 * pad)) * 10) / 10]);
}

/** Bar heights in px for a list of non-negative numbers; the tallest bar gets maxPx, zero stays zero. */
export function barHeights(values, maxPx = 120) {
  const max = Math.max(1, ...values.map((v) => Number(v) || 0));
  return values.map((v) => Math.round(((Number(v) || 0) / max) * maxPx));
}

export const countByLevel = (people) => LEVELS.map((l) => (people || []).filter((p) => p.level === l).length);

/** Line series that may contain gaps (null = no data that day). Returns { segments: [[[x, y], ...], ...], max }; each run of numbers is one segment. */
export function seriesPoints(values, w = 300, h = 80, pad = 6) {
  const nums = values.filter((v) => typeof v === "number"); const max = Math.max(1, ...nums);
  const step = values.length > 1 ? (w - 2 * pad) / (values.length - 1) : 0; const segments = []; let cur = [];
  values.forEach((v, i) => {
    if (typeof v !== "number") { if (cur.length) segments.push(cur); cur = []; return; }
    cur.push([Math.round((pad + i * step) * 10) / 10, Math.round((h - pad - (v / max) * (h - 2 * pad)) * 10) / 10]);
  });
  if (cur.length) segments.push(cur); return { segments, max };
}
