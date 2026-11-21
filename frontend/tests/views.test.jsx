// Server-side render tests: every state (loading / error / empty / data) in English and Arabic. Effects (network) do not run in static rendering,
// so these check what the screen shows for a given state; the data flow itself needs the backend (see docs/TESTING_REPORT.md).
import test from "node:test";
import assert from "node:assert/strict";
import { renderToStaticMarkup } from "react-dom/server";
import { I18nProvider } from "../src/i18n.jsx";
import { Status, Sparkline, Bars } from "../src/components.jsx";
import { AlertsView, CarePlansView, CheckinsView, EventsView, OverviewView } from "../src/pages.jsx";
import { AnalyticsView, Dashboard, Login, NotificationsView, Settings, TimelineView, Admin } from "../src/App.jsx";
globalThis.localStorage = { _m: {}, getItem(k) { return this._m[k] ?? null; }, setItem(k, v) { this._m[k] = String(v); }, removeItem(k) { delete this._m[k]; } };
const view = (el, lang = "en") => { localStorage.setItem("ui_lang", lang); return renderToStaticMarkup(<I18nProvider>{el}</I18nProvider>); };
const noRawKeys = (html) => assert.doesNotMatch(html, /\b(state|tl|evt|ana|notif|dash|auth|trend|settings|admin)\.[a-z_]+\b/, "an untranslated key is visible");
const data = { total_alerts: 3, falls: 2, checkin_failures: 1, avg_response_min: 4, false_alarm_rate: 33, alerts_per_day: { "2026-11-18": 1, "2026-11-19": 2 }, falls_by_hour: Array(24).fill(0) };
for (const lang of ["en", "ar"]) {
  test(`Status shows loading, error with retry, empty and children [${lang}]`, () => {
    assert.match(view(<Status loading />, lang), /aria-busy="true"/);
    const e = view(<Status error="boom" onRetry={() => {}} />, lang); assert.match(e, /role="alert"/); assert.match(e, /boom/); assert.match(e, /<button/);
    assert.match(view(<Status empty emptyText="nothing here" />, lang), /nothing here/); assert.match(view(<Status><b>ok</b></Status>, lang), /<b>ok<\/b>/);
  });
  test(`Analytics: loading, error and data [${lang}]`, () => {
    assert.match(view(<AnalyticsView data={null} />, lang), /aria-busy/);
    assert.match(view(<AnalyticsView data={null} error="Server down" onRetry={() => {}} />, lang), /Server down/);
    const h = view(<AnalyticsView data={data} info={null} levels={[1, 0, 0, 2, 0]} />, lang); assert.match(h, /role="img"/); assert.match(h, /alerts\.csv/); noRawKeys(h);
  });
  test(`Notifications: loading, error, empty, rows [${lang}]`, () => {
    assert.match(view(<NotificationsView rows={[]} loaded={false} />, lang), /aria-busy/); assert.match(view(<NotificationsView rows={[]} loaded error="x" />, lang), /role="alert"/);
    noRawKeys(view(<NotificationsView rows={[]} loaded />, lang)); assert.match(view(<NotificationsView rows={[{ id: 1, text: "Fall alert for Mona", at: "2026-11-19T10:00:00" }]} loaded />, lang), /Fall alert for Mona/);
  });
  test(`Timeline: loading, empty, data [${lang}]`, () => {
    assert.match(view(<TimelineView data={null} />, lang), /aria-busy/); noRawKeys(view(<TimelineView data={{ events: [], checkins: [] }} />, lang));
    const h = view(<TimelineView data={{ events: [{ id: 1, kind: "fall", value: .9, at: "2026-11-19T10:00:00" }], checkins: [{ id: 1, scheduled_at: "2026-11-19T09:00:00", responded_at: null }] }} />, lang);
    assert.match(h, /data-kind="fall"/); assert.match(h, /overdue/); noRawKeys(h);
  });
  test(`Login, Settings, Admin and Dashboard first render without raw keys [${lang}]`, () => {
    noRawKeys(view(<Login onDone={() => {}} />, lang)); noRawKeys(view(<Settings />, lang)); noRawKeys(view(<Admin />, lang));
    const d = view(<Dashboard me={{ role: "admin", username: "admin" }} />, lang); assert.match(d, /aria-busy/); noRawKeys(d);
  });
}
test("Arabic renders Arabic text", () => { assert.match(view(<Status loading />, "ar"), /[\u0600-\u06FF]/); });
test("Sparkline needs two readings; draws a polyline otherwise", () => {
  assert.match(view(<Sparkline history={[{ level: "Low" }]} />), /Not enough history/);
  const h = view(<Sparkline history={[{ level: "High" }, { level: "Low" }, { level: "Normal" }]} />); assert.match(h, /<polyline/); assert.match(h, /aria-label="Risk level over 3 readings, latest: High"/);
});
test("Bars: heights proportional, thin variant hides the numbers", () => {
  const h = view(<Bars items={[{ key: "a", label: "a", value: 0 }, { key: "b", label: "b", value: 4 }]} maxPx={80} title="t" />); assert.match(h, /height:0px/); assert.match(h, /height:80px/);
  assert.doesNotMatch(view(<Bars thin items={[{ key: "a", label: "a", value: 7 }]} title="t" />), /<span>7<\/span>/);
});

const summary = { totals: { people: 3, caregivers: 1 }, safety: { status: "critical", levels: { Normal: 1, Low: 0, Medium: 0, High: 1, Critical: 1 } },
  alerts: { open: 2, high_or_critical_open: 2, acknowledged: 0, per_day: { "2026-11-20": 1, "2026-11-21": 1 } }, checkins_today: { due: 3, answered: 1, missed: 1, pending: 1 },
  falls: { today: 1, last_7_days: 2, per_day: { "2026-11-20": 1, "2026-11-21": 1 } }, activity_trend: [{ day: "2026-11-20", mean: 40, n: 3 }, { day: "2026-11-21", mean: null, n: 0 }, { day: "2026-11-22", mean: 25, n: 2 }],
  anomalies: [{ elderly_id: 1, name: "Mona", kind: "activity_drop", ratio: 0.3 }, { elderly_id: 2, name: "Omar", kind: "missed_checkin", ratio: null }],
  recent_events: [{ id: 1, elderly_id: 1, name: "Mona", kind: "fall", value: .9, at: "2026-11-21T10:00:00" }],
  caregivers: [{ id: 7, username: "sara", people: 2, open_alerts: 1, resolved_7d: 3, avg_response_min: 4.5 }] };
for (const lang of ["en", "ar"]) {
  test(`Overview shows every KPI from backend data, no raw keys [${lang}]`, () => {
    const h = view(<OverviewView data={summary} />, lang); noRawKeys(h); assert.match(h, /data-status="critical"/); assert.match(h, />2<\/b>/); assert.match(h, /2\/3|1\/3/);
    assert.match(h, /Mona/); assert.match(h, /sara/); assert.match(h, /<polyline|<circle/); assert.match(h, /role="img"/);
    assert.match(view(<OverviewView data={null} />, lang), /aria-busy/); assert.match(view(<OverviewView data={null} error="down" onRetry={() => {}} />, lang), /down/);
  });
  test(`Overview with nothing to show [${lang}]`, () => {
    const empty = { ...summary, totals: { people: 0, caregivers: 0 }, safety: { status: "ok", levels: { Normal: 0, Low: 0, Medium: 0, High: 0, Critical: 0 } }, anomalies: [], recent_events: [], caregivers: [], activity_trend: [{ day: "2026-11-21", mean: null, n: 0 }] };
    noRawKeys(view(<OverviewView data={empty} />, lang));
  });
  test(`Alerts page: filter, empty, acknowledge button only for open [${lang}]`, () => {
    const rows = [{ id: 1, name: "Mona", level: "High", status: "open", stage: 2, stage_text: "Caregiver notified", reasons: "No answer", created_at: "2026-11-21T10:00:00" }, { id: 2, name: "Omar", level: "Low", status: "resolved", stage: 1, stage_text: "x", reasons: "ok", created_at: "2026-11-20T10:00:00" }];
    const all = view(<AlertsView rows={rows} status="all" setStatus={() => {}} onAck={() => {}} />, lang); assert.equal((all.match(/<button/g) || []).length, 1); noRawKeys(all);
    assert.doesNotMatch(view(<AlertsView rows={rows} status="open" setStatus={() => {}} onAck={() => {}} />, lang), /Omar/);
    noRawKeys(view(<AlertsView rows={[]} status="all" setStatus={() => {}} onAck={() => {}} />, lang)); assert.match(view(<AlertsView rows={null} status="all" setStatus={() => {}} />, lang), /aria-busy/);
  });
  test(`Events and Check-ins tables [${lang}]`, () => {
    const f = { person: "", kind: "", status: "" };
    const e = view(<EventsView rows={[{ id: 1, name: "Mona", kind: "fall", value: .91, at: "2026-11-21T10:00:00" }]} people={[{ id: 1, name: "Mona" }]} filters={f} setFilters={() => {}} />, lang); assert.match(e, /91%/); noRawKeys(e);
    noRawKeys(view(<EventsView rows={[]} people={[]} filters={f} setFilters={() => {}} />, lang));
    const c = view(<CheckinsView rows={[{ id: 1, name: "Omar", status: "missed", scheduled_at: "2026-11-21T09:00:00", responded_at: null }]} people={[]} filters={f} setFilters={() => {}} />, lang); assert.match(c, /class="missed"/); noRawKeys(c);
    assert.match(view(<CheckinsView rows={null} people={null} filters={f} setFilters={() => {}} />, lang), /aria-busy/);
  });
  test(`Care plans: add form, toggle and remove buttons are wired [${lang}]`, () => {
    const g = [{ elderly_id: 1, name: "Mona", items: [{ id: 5, kind: "medication", title: "Evening pill", time: "20:00", note: "", done_today: false, overdue: true }] }, { elderly_id: 2, name: "Omar", items: [] }];
    const h = view(<CarePlansView groups={g} form={{ person: "", kind: "medication", title: "", time: "09:00" }} setForm={() => {}} onAdd={() => {}} onToggle={() => {}} onRemove={() => {}} />, lang);
    assert.match(h, /Evening pill/); assert.match(h, /class="overdue"/); assert.match(h, /type="submit"/); assert.match(h, /type="time"/); noRawKeys(h);
    noRawKeys(view(<CarePlansView groups={[]} form={{ person: "", kind: "meal", title: "", time: "09:00" }} setForm={() => {}} />, lang));
  });
}
