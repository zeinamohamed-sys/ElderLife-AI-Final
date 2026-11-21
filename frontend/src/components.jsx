import { useI18n } from "./i18n.jsx";
import { barHeights, levelIndex, LEVELS, seriesPoints, trendPoints } from "./lib/charts.js";

/** One place for the loading / error / empty states, so no page can show a blank screen when something goes wrong. */
export function Status({ loading, error, empty, emptyText, onRetry, children }) {
  const { t } = useI18n();
  if (loading) return <p className="empty" role="status" aria-busy="true">{t("state.loading")}</p>;
  if (error) return (
    <div className="error-box" role="alert"><p className="error">{error}</p>{onRetry && <button type="button" onClick={onRetry}>{t("state.retry")}</button>}</div>
  );
  if (empty) return <p className="empty">{emptyText}</p>;
  return children;
}

/** Risk level over time (oldest -> newest) as a small line chart. */
export function Sparkline({ history }) {
  const { t } = useI18n();
  const pts = trendPoints(history);
  if (pts.length < 2) return <p className="empty">{t("trend.not_enough")}</p>;
  const last = history[0];
  return (
    <svg className="spark" viewBox="0 0 220 48" role="img" aria-label={t("trend.aria", { n: pts.length, level: t("level." + last.level) })}>
      {[0, 1, 2, 3, 4].map((i) => <line key={i} x1="0" x2="220" y1={4 + (1 - i / 4) * 40} y2={4 + (1 - i / 4) * 40} className="grid" />)}
      <polyline points={pts.map((p) => p.join(",")).join(" ")} fill="none" strokeWidth="2" className="line" data-level={LEVELS[levelIndex(last.level)]} />
      {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="2.5" className="pt" />)}
    </svg>
  );
}

/** Vertical bars with the value on top and a label below. items: [{ key, label, value, level? }] */
export function Bars({ items, thin = false, maxPx = 120, title }) {
  const hs = barHeights(items.map((i) => i.value), maxPx);
  return (
    <div className={thin ? "chart thin" : "chart"} role="img" aria-label={title}>
      {items.map((it, i) => (
        <div key={it.key}>{!thin && <span>{it.value}</span>}<i data-level={it.level} style={{ height: `${hs[i]}px` }} title={title ? `${title}: ${it.value}` : String(it.value)} /><small>{it.label}</small></div>
      ))}
    </div>
  );
}

/** Line chart with gaps. values: numbers or null; labels: x-axis text for the first/last point. */
export function LineChart({ values, labels, title }) {
  const { segments, max } = seriesPoints(values);
  const none = segments.length === 0;
  return (
    <figure className="linechart">
      <svg viewBox="0 0 300 80" role="img" aria-label={title}>
        <line x1="0" x2="300" y1="74" y2="74" className="grid" /><line x1="0" x2="300" y1="6" y2="6" className="grid" />
        {segments.map((seg, i) => seg.length > 1
          ? <polyline key={i} points={seg.map((p) => p.join(",")).join(" ")} fill="none" strokeWidth="2" className="line" />
          : <circle key={i} cx={seg[0][0]} cy={seg[0][1]} r="3" className="pt" />)}
      </svg>
      <figcaption>{none ? "" : `max ${max}`}{labels && <span>{labels[0]} {"->"} {labels[labels.length - 1]}</span>}</figcaption>
    </figure>
  );
}
