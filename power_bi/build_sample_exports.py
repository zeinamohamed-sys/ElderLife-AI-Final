"""Writes SYNTHETIC sample CSVs with exactly the columns of the backend's /export/* endpoints (24 people, 60 days) into power_bi/sample_data/.
They exist only to design the Power BI report before a backend is running. They are NOT real data. Run: python power_bi/build_sample_exports.py"""
import csv, pathlib, random
from datetime import datetime, timedelta
OUT = pathlib.Path(__file__).parent / "sample_data"; OUT.mkdir(exist_ok=True)
rng = random.Random(7); end = datetime(2026, 11, 20, 18, 0); start = end - timedelta(days=60); LEVELS = ["Normal", "Low", "Medium", "High", "Critical"]
REASONS = ["No answer to the daily check-in for 2 hours", "Activity far below this person's usual level", "Fall detected and nobody answered", "Help button pressed", "Missed 2 reminders today"]
def w(name, header, rows):
    with open(OUT / f"sample_{name}.csv", "w", newline="", encoding="utf-8") as f: cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
people = [(i, rng.randint(66, 94), round(rng.uniform(25, 70), 1), rng.choice(["08:00", "09:00", "10:00"]), 1 + i % 4) for i in range(1, 25)]
w("people", ["elderly_id", "age", "baseline_activity", "checkin_time", "caregiver_id"], people)
events, alerts, risk, checkins, plan = [], [], [], [], []; eid_row = aid = cid = iid = 0
for (pid, age, base, ct, cg) in people:
    for d in range(60):
        day = start + timedelta(days=d)
        for h in range(7, 22, 2):
            eid_row += 1; events.append((eid_row, pid, "activity", round(max(0, rng.gauss(base, base * .2)), 1), (day.replace(hour=h, minute=rng.randint(0, 59))).isoformat(sep=" ")))
        hh, mm = map(int, ct.split(":")); sched = day.replace(hour=hh, minute=mm); cid += 1; ans = rng.random() > .06
        checkins.append((cid, pid, sched.isoformat(sep=" "), (sched + timedelta(minutes=rng.randint(1, 40))).isoformat(sep=" ") if ans else ""))
        lvl = "Normal" if rng.random() < .85 else rng.choice(LEVELS[1:3]); risk.append((pid, lvl, round(LEVELS.index(lvl) * .15 + rng.random() * .1, 2), (sched + timedelta(hours=1)).isoformat(sep=" ")))
        if rng.random() < .012:
            t = day.replace(hour=rng.randint(0, 23), minute=rng.randint(0, 59)); eid_row += 1; events.append((eid_row, pid, "fall", round(rng.uniform(.6, 1), 2), t.isoformat(sep=" ")))
            aid += 1; by = rng.choice(["person", "caregiver", "caregiver"]); alerts.append((aid, pid, rng.choice(["High", "Critical"]), REASONS[2], "resolved", rng.randint(1, 3), by, t.isoformat(sep=" "), (t + timedelta(minutes=rng.randint(1, 25))).isoformat(sep=" ")))
        elif not ans and rng.random() < .5:
            aid += 1; t = sched + timedelta(hours=2); alerts.append((aid, pid, "Medium", REASONS[0], "resolved", 2, "caregiver", t.isoformat(sep=" "), (t + timedelta(minutes=rng.randint(5, 40))).isoformat(sep=" ")))
    for kind, title, tm in (("medication", "Morning pill", "08:30"), ("meal", "Lunch", "13:00"), ("water", "Drink water", "16:00")):
        iid += 1; plan.append((iid, pid, kind, title, tm, "2026-11-20" if rng.random() < .7 else ""))
w("alerts", ["id", "elderly_id", "level", "reasons", "status", "stage", "resolved_by", "created_at", "resolved_at"], alerts); w("risk", ["elderly_id", "level", "score", "created_at"], risk)
w("events", ["id", "elderly_id", "kind", "value", "created_at"], events); w("checkins", ["id", "elderly_id", "scheduled_at", "responded_at"], checkins); w("careplan", ["id", "elderly_id", "kind", "title", "time", "done_date"], plan)
print({k: len(v) for k, v in dict(people=people, alerts=alerts, risk=risk, events=events, checkins=checkins, careplan=plan).items()})
