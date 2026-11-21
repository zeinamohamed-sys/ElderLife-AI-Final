"""CASAS smart-home event logs -> one row per home-day (hourly motion and door counts).
Input: one text/CSV file per home, one sensor event per line: <date> <time> <sensor-id> <message> [activity label tokens...]
(whitespace or comma separated; e.g.  2010-11-04 00:03:50.209589 M003 ON). Sources/terms: ml/data/DATASETS_REGISTRY.md.
Cleaning: unparsable lines dropped, exact duplicate events dropped, sorted by time; only ON/OPEN/PRESENT messages count as events (numeric readings such as
temperature are ignored); motion sensors = ids matching --motion-regex (default ^M\\d+), door sensors = --door-regex (default ^D\\d+). If a file has no sensor
matching the motion regex, ALL non-door binary events are used and the report says so (mapped-name datasets).
Usage:  python -m ml.preprocessing.casas <dir_or_file> [--out ml/data/processed/casas_days.csv.gz] [--min-events-per-day 20]
Days with fewer events than the minimum (logging gaps, empty homes) are dropped, and the first/last partial day of each home is dropped."""
import argparse, json, pathlib, re
import numpy as np, pandas as pd
ON = {"ON", "OPEN", "PRESENT", "1"}
def parse_events(path):
    rows, bad = [], 0
    for line in pathlib.Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        t = re.split(r"[,\s]+", line.strip())
        if len(t) < 4: bad += 1; continue
        rows.append((t[0] + " " + t[1], t[2], t[3].upper()))
    df = pd.DataFrame(rows, columns=["ts", "sensor", "msg"]); df["ts"] = pd.to_datetime(df.ts, format="mixed", errors="coerce")   # CASAS logs mix "...:50" and "...:50.209589" timestamps
    n0 = len(df); df = df.dropna(subset=["ts"]).drop_duplicates().sort_values("ts")
    return df.reset_index(drop=True), {"lines_unparsable": bad + (n0 - len(df.dropna(subset=['ts']))), "events_after_cleaning": int(len(df))}
def daily_table(ev, motion_re=r"^M\d+", door_re=r"^D\d+", min_events=20):
    ev = ev[ev.msg.isin(ON)].copy(); note = ""
    is_door = ev.sensor.str.match(door_re); is_motion = ev.sensor.str.match(motion_re)
    if not is_motion.any(): is_motion = ~is_door; note = "no sensor matched the motion regex: all non-door ON events were used as motion"
    ev["day"] = ev.ts.dt.normalize(); ev["hour"] = ev.ts.dt.hour
    days = pd.date_range(ev.day.min(), ev.day.max(), freq="D") if len(ev) else []
    M = ev[is_motion].groupby(["day", "hour"]).size().unstack(fill_value=0).reindex(index=days, columns=range(24), fill_value=0)
    D = ev[is_door].groupby(["day", "hour"]).size().unstack(fill_value=0).reindex(index=days, columns=range(24), fill_value=0)
    out = pd.concat([M.add_prefix("m"), D.add_prefix("d")], axis=1); out.index.name = "day"
    out = out.iloc[1:-1] if len(out) > 2 else out                     # first and last day are partial
    out = out[(M.loc[out.index].sum(axis=1) + D.loc[out.index].sum(axis=1)) >= min_events]
    return out.reset_index(), note
def features(days):
    """Daily behaviour features from hourly counts. Works on a table with columns m0..m23, d0..d23."""
    M = days[[f"m{h}" for h in range(24)]].to_numpy(float); D = days[[f"d{h}" for h in range(24)]].to_numpy(float); tot = M.sum(1)
    p = M / np.maximum(tot[:, None], 1); ent = -(p * np.log(p + 1e-12)).sum(1)
    act = M > 0; first = np.where(act.any(1), act.argmax(1), 12); last = np.where(act.any(1), 23 - act[:, ::-1].argmax(1), 12)
    return pd.DataFrame({"total_motion": tot, "night_motion": M[:, 0:5].sum(1), "morning_motion": M[:, 5:12].sum(1), "evening_motion": M[:, 18:24].sum(1),
                         "active_hours": act.sum(1), "first_hour": first, "last_hour": last, "hourly_entropy": ent, "door_total": D.sum(1)}, index=days.index)
FEATURES = ["total_motion", "night_motion", "morning_motion", "evening_motion", "active_hours", "first_hour", "last_hour", "hourly_entropy", "door_total"]
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--out", default="ml/data/processed/casas_days.csv.gz"); ap.add_argument("--motion-regex", default=r"^M\d+")
    ap.add_argument("--door-regex", default=r"^D\d+"); ap.add_argument("--min-events-per-day", type=int, default=20); a = ap.parse_args()
    p = pathlib.Path(a.src); files = [p] if p.is_file() else sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in (".csv", ".txt", ".dat", ""))
    parts, report = [], {}
    for f in files:
        ev, info = parse_events(f)
        if ev.empty: report[f.stem] = {**info, "skipped": "no parsable events"}; continue
        d, note = daily_table(ev, a.motion_regex, a.door_regex, a.min_events_per_day)
        if d.empty: report[f.stem] = {**info, "skipped": "no day with enough events"}; continue
        d.insert(0, "home", f.stem); parts.append(d); report[f.stem] = {**info, "days_kept": int(len(d)), "note": note}
    if not parts: raise SystemExit("no usable CASAS data found")
    out = pd.concat(parts, ignore_index=True); pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True); out.to_csv(a.out, index=False)
    print(json.dumps(report, indent=1)); print(f"{len(out)} home-days from {out.home.nunique()} homes -> {a.out}")
if __name__ == "__main__": main()
