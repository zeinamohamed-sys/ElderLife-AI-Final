import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import { useI18n } from "./i18n.jsx";
import { Bars, LineChart, Status } from "./components.jsx";
import { LEVELS } from "./lib/charts.js";

const usePolling = (path, ms = 10000) => {
  const [data, setData] = useState(null); const [error, setError] = useState("");
  const load = useCallback(async () => { try { setData(await api(path)); setError(""); } catch (x) { setError(x.message); } }, [path]);
  useEffect(() => { load(); const id = setInterval(load, ms); return () => clearInterval(id); }, [load, ms]);
  return { data, error, load };
};

/* ---------------- Overview (main dashboard) ---------------- */
export function OverviewView({ data: d, error, onRetry }) {
  const { t, fmt } = useI18n();
  return (
    <section className="overview">
      <h2>{t("ov.title")}</h2>
      <Status loading={!d && !error} error={error} onRetry={onRetry}>
        {d && (<>
          <div className="kpis">
            <div className="kpi" data-status={d.safety.status}><small>{t("ov.status")}</small><b>{t("ov.status." + d.safety.status)}</b></div>
            <div className="kpi"><small>{t("ov.people")}</small><b>{d.totals.people}</b></div>
            <div className="kpi" data-warn={d.alerts.open > 0}><small>{t("ov.open_alerts")}</small><b>{d.alerts.open}</b><span>{t("ov.high_open", { n: d.alerts.high_or_critical_open })}</span></div>
            <div className="kpi"><small>{t("ov.checkins")}</small><b>{d.checkins_today.answered}/{d.checkins_today.due}</b><span>{t("ov.checkins_detail", d.checkins_today)}</span></div>
            <div className="kpi" data-warn={d.falls.today > 0}><small>{t("ov.falls")}</small><b>{d.falls.today}</b><span>{t("ov.falls_week", { n: d.falls.last_7_days })}</span></div>
            <div className="kpi" data-warn={d.anomalies.length > 0}><small>{t("ov.anomalies")}</small><b>{d.anomalies.length}</b></div>
          </div>
          <div className="grid2">
            <div><h3>{t("ov.risk_levels")}</h3>
              <Bars title={t("ov.risk_levels")} items={LEVELS.map((l) => ({ key: l, label: t("level." + l), value: d.safety.levels[l], level: l }))} /></div>
            <div><h3>{t("ov.alerts_week")}</h3>
              <Bars title={t("ov.alerts_week")} items={Object.entries(d.alerts.per_day).map(([day, n]) => ({ key: day, label: day.slice(5), value: n }))} /></div>
            <div><h3>{t("ov.falls_chart")}</h3>
              <Bars title={t("ov.falls_chart")} items={Object.entries(d.falls.per_day).map(([day, n]) => ({ key: day, label: day.slice(5), value: n }))} /></div>
            <div><h3>{t("ov.activity")}</h3>
              <LineChart title={t("ov.activity")} values={d.activity_trend.map((x) => x.mean)} labels={[d.activity_trend[0].day.slice(5), d.activity_trend[d.activity_trend.length - 1].day.slice(5)]} />
              <p className="note">{t("ov.activity_note")}</p></div>
          </div>
          <h3>{t("ov.anomalies")}</h3>
          {d.anomalies.length === 0 ? <p className="empty">{t("ov.no_anomalies")}</p> :
            <ul className="anoms">{d.anomalies.map((a, i) => <li key={i}>{t("ov.anom." + a.kind, { name: a.name, pct: a.ratio != null ? Math.round(a.ratio * 100) : "" })}</li>)}</ul>}
          <h3>{t("ov.recent")}</h3>
          {d.recent_events.length === 0 ? <p className="empty">{t("ev.empty")}</p> :
            <ul className="events">{d.recent_events.map((e) => <li key={e.id} data-kind={e.kind}><b>{e.name}</b> {t("evt." + e.kind)} <small>{fmt(e.at)}</small></li>)}</ul>}
          {d.caregivers.length > 0 && (<>
            <h3>{t("ov.caregivers")}</h3>
            <div className="scroll"><table><thead><tr><th>{t("admin.username")}</th><th>{t("ov.cg_people")}</th><th>{t("ov.cg_open")}</th><th>{t("ov.cg_resolved")}</th><th>{t("ov.cg_response")}</th></tr></thead>
              <tbody>{d.caregivers.map((c) => <tr key={c.id}><td>{c.username}</td><td>{c.people}</td><td>{c.open_alerts}</td><td>{c.resolved_7d}</td><td>{c.avg_response_min ?? "-"}</td></tr>)}</tbody></table></div>
          </>)}
        </>)}
      </Status>
    </section>
  );
}
export function Overview() { const { data, error, load } = usePolling("/dashboard/summary"); return <OverviewView data={data} error={error} onRetry={load} />; }

/* ---------------- Alerts ---------------- */
export function AlertsView({ rows, error, onRetry, onAck, status, setStatus }) {
  const { t, fmt } = useI18n();
  const shown = rows ? rows.filter((a) => status === "all" || a.status === status) : [];
  return (
    <section>
      <h2>{t("al.title")}</h2>
      <label>{t("al.filter")} <select value={status} onChange={(e) => setStatus(e.target.value)}>
        {["all", "open", "acknowledged", "resolved"].map((s) => <option key={s} value={s}>{s === "all" ? t("al.all") : t("status." + s)}</option>)}</select></label>
      <Status loading={!rows && !error} error={error} empty={rows && shown.length === 0} emptyText={t("al.empty")} onRetry={onRetry}>
        <ul className="alerts">{shown.map((a) => (
          <li key={a.id} data-level={a.level}>
            <div><b>{a.name}</b> <span className="lvl">{t("level." + a.level)}</span> <small>{t("status." + a.status)} - {a.stage_text}</small><p>{a.reasons}</p><small className="when">{fmt(a.created_at)}</small></div>
            {a.status === "open" && <button onClick={() => onAck(a.id)}>{t("dash.acknowledge")}</button>}
          </li>))}</ul>
      </Status>
    </section>
  );
}
export function AlertsPage() {
  const [status, setStatus] = useState("all"); const [err, setErr] = useState(""); const { data, error, load } = usePolling("/alerts", 5000);
  const ack = async (id) => { try { await api(`/alerts/${id}/ack`, "POST"); setErr(""); } catch (x) { setErr(x.message); } load(); };
  return <AlertsView rows={data} error={error || err} onRetry={load} onAck={ack} status={status} setStatus={setStatus} />;
}

/* ---------------- Events ---------------- */
export function EventsView({ rows, people, error, onRetry, filters, setFilters }) {
  const { t, fmt } = useI18n();
  return (
    <section>
      <h2>{t("ev.title")}</h2>
      <div className="filters">
        <label>{t("ev.filter_person")} <select value={filters.person} onChange={(e) => setFilters({ ...filters, person: e.target.value })}>
          <option value="">{t("ev.all_people")}</option>{(people || []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        <label>{t("ev.filter_kind")} <select value={filters.kind} onChange={(e) => setFilters({ ...filters, kind: e.target.value })}>
          <option value="">{t("ev.all_kinds")}</option>{["activity", "fall", "ok", "sos"].map((k) => <option key={k} value={k}>{t("evt." + k)}</option>)}</select></label>
      </div>
      <Status loading={!rows && !error} error={error} empty={rows && rows.length === 0} emptyText={t("ev.empty")} onRetry={onRetry}>
        <div className="scroll"><table><thead><tr><th>{t("ev.when")}</th><th>{t("al.person")}</th><th>{t("ev.what")}</th><th>{t("ev.value")}</th></tr></thead>
          <tbody>{(rows || []).map((e) => <tr key={e.id} data-kind={e.kind}><td>{fmt(e.at)}</td><td>{e.name}</td><td>{t("evt." + e.kind)}</td><td>{e.kind === "fall" ? `${Math.round((e.value || 0) * 100)}%` : e.value}</td></tr>)}</tbody></table></div>
      </Status>
    </section>
  );
}
export function EventsPage() {
  const [filters, setFilters] = useState({ person: "", kind: "" }); const people = usePolling("/elderly", 60000);
  const q = new URLSearchParams({ limit: "100", ...(filters.person ? { elderly_id: filters.person } : {}), ...(filters.kind ? { kind: filters.kind } : {}) });
  const { data, error, load } = usePolling(`/events?${q}`);
  return <EventsView rows={data} people={people.data} error={error} onRetry={load} filters={filters} setFilters={setFilters} />;
}

/* ---------------- Check-ins ---------------- */
export function CheckinsView({ rows, people, error, onRetry, filters, setFilters }) {
  const { t, fmt } = useI18n();
  return (
    <section>
      <h2>{t("ci.title")}</h2>
      <div className="filters">
        <label>{t("ev.filter_person")} <select value={filters.person} onChange={(e) => setFilters({ ...filters, person: e.target.value })}>
          <option value="">{t("ev.all_people")}</option>{(people || []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        <label>{t("al.filter")} <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">{t("al.all")}</option>{["answered", "missed", "pending"].map((s) => <option key={s} value={s}>{t("ci.status." + s)}</option>)}</select></label>
      </div>
      <Status loading={!rows && !error} error={error} empty={rows && rows.length === 0} emptyText={t("ci.empty")} onRetry={onRetry}>
        <div className="scroll"><table><thead><tr><th>{t("al.person")}</th><th>{t("ci.scheduled")}</th><th>{t("al.filter")}</th><th>{t("ci.answered_at")}</th></tr></thead>
          <tbody>{(rows || []).map((c) => <tr key={c.id} className={c.status}><td>{c.name}</td><td>{fmt(c.scheduled_at)}</td><td>{t("ci.status." + c.status)}</td><td>{c.responded_at ? fmt(c.responded_at) : "-"}</td></tr>)}</tbody></table></div>
      </Status>
    </section>
  );
}
export function CheckinsPage() {
  const [filters, setFilters] = useState({ person: "", status: "" }); const people = usePolling("/elderly", 60000);
  const q = new URLSearchParams({ limit: "100", ...(filters.person ? { elderly_id: filters.person } : {}), ...(filters.status ? { status: filters.status } : {}) });
  const { data, error, load } = usePolling(`/checkins?${q}`);
  return <CheckinsView rows={data} people={people.data} error={error} onRetry={load} filters={filters} setFilters={setFilters} />;
}

/* ---------------- Care plans ---------------- */
export function CarePlansView({ groups, error, onRetry, onToggle, onRemove, onAdd, form, setForm }) {
  const { t } = useI18n();
  return (
    <section>
      <h2>{t("cp.title")}</h2>
      <p className="note">{t("dash.careplan_note")}</p>
      {groups && groups.length > 0 && (
        <form className="inline" onSubmit={(e) => { e.preventDefault(); onAdd(); }}>
          <select aria-label={t("al.person")} value={form.person} onChange={(e) => setForm({ ...form, person: e.target.value })} required>
            <option value="">{t("al.person")}</option>{groups.map((g) => <option key={g.elderly_id} value={g.elderly_id}>{g.name}</option>)}</select>
          <select aria-label={t("cp.kind")} value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>{["medication", "meal", "water", "activity"].map((k) => <option key={k} value={k}>{t("kind." + k)}</option>)}</select>
          <input aria-label={t("cp.what")} placeholder={t("cp.what")} value={form.title} maxLength={100} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          <input type="time" aria-label={t("cp.time")} value={form.time} onChange={(e) => setForm({ ...form, time: e.target.value })} required />
          <button type="submit">{t("dash.add_reminder")}</button>
        </form>)}
      <Status loading={!groups && !error} error={error} empty={groups && groups.length === 0} emptyText={t("dash.empty_caregiver")} onRetry={onRetry}>
        {(groups || []).map((g) => (
          <div key={g.elderly_id} className="plan"><h3>{g.name}</h3>
            {g.items.length === 0 ? <p className="empty">{t("cp.empty")}</p> :
              <ul className="care">{g.items.map((i) => (
                <li key={i.id} className={i.done_today ? "done" : i.overdue ? "overdue" : ""}>
                  <span>{i.time} <b>{i.title}</b> <small>{t("kind." + i.kind)}{i.overdue ? ` - ${t("dash.overdue")}` : ""}</small></span>
                  <button onClick={() => onToggle(i.id)}>{i.done_today ? t("cp.undo") : t("cp.mark")}</button>
                  <button aria-label={t("dash.remove", { title: i.title })} onClick={() => onRemove(i.id)}>{t("dash.remove_btn")}</button>
                </li>))}</ul>}
          </div>))}
      </Status>
    </section>
  );
}
export function CarePlansPage() {
  const [form, setForm] = useState({ person: "", kind: "medication", title: "", time: "09:00" }); const [err, setErr] = useState(""); const { data, error, load } = usePolling("/careplan", 15000);
  const run = async (fn) => { try { await fn(); setErr(""); } catch (x) { setErr(x.message); } load(); };
  return <CarePlansView groups={data} error={error || err} onRetry={load} form={form} setForm={setForm}
    onToggle={(id) => run(() => api(`/careplan/${id}/done`, "POST"))} onRemove={(id) => run(() => api(`/careplan/${id}`, "DELETE"))}
    onAdd={() => run(async () => { await api(`/elderly/${form.person}/careplan`, "POST", { kind: form.kind, title: form.title, time: form.time }); setForm({ ...form, title: "" }); })} />;
}
