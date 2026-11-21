"""Dashboard numbers computed from plain rows (dicts), so the maths is testable without a database. api/dashboard.py gathers the rows.
Everything here is derived from real stored data: nothing is hard-coded or demo."""
from datetime import timedelta
LEVELS = ["Normal", "Low", "Medium", "High", "Critical"]
LATE_MIN = 30          # a check-in unanswered this long after its time counts as missed
ACTIVITY_DROP = 0.6    # today's mean activity below 60% of the person's baseline = behavioural anomaly

def _day(d): return d.strftime("%Y-%m-%d")

def build_summary(people, alerts, events, checkins, caregivers, now, days=14):
    """people: [{id,name,level,score,baseline,caregiver_id}]  alerts: [{id,elderly_id,level,status,created_at,resolved_at,resolved_by}]
    events: [{id,elderly_id,kind,value,created_at}]  checkins: [{elderly_id,scheduled_at,responded_at}]  caregivers: [{id,username}]"""
    name = {p["id"]: p["name"] for p in people}; today = _day(now)
    levels = {l: 0 for l in LEVELS}
    for p in people: levels[p["level"]] = levels.get(p["level"], 0) + 1
    open_a = [a for a in alerts if a["status"] == "open"]; ack_a = [a for a in alerts if a["status"] == "acknowledged"]
    crit_open = [a for a in open_a if a["level"] in ("High", "Critical")]
    status = "critical" if any(a["level"] == "Critical" for a in open_a) or levels["Critical"] else "attention" if (open_a or ack_a or levels["High"] or levels["Medium"]) else "ok"
    d7 = [_day(now - timedelta(days=i)) for i in range(6, -1, -1)]
    per_day = {d: 0 for d in d7}
    for a in alerts:
        if _day(a["created_at"]) in per_day: per_day[_day(a["created_at"])] += 1
    falls = [e for e in events if e["kind"] == "fall"]; fall_day = {d: 0 for d in d7}
    for e in falls:
        if _day(e["created_at"]) in fall_day: fall_day[_day(e["created_at"])] += 1
    # check-ins scheduled today
    due = [c for c in checkins if _day(c["scheduled_at"]) == today]
    answered = [c for c in due if c["responded_at"]]; missed = [c for c in due if not c["responded_at"] and c["scheduled_at"] < now - timedelta(minutes=LATE_MIN)]
    # activity trend: mean of 'activity' event values per day over the last `days` days
    dN = [_day(now - timedelta(days=i)) for i in range(days - 1, -1, -1)]; acc = {d: [] for d in dN}
    for e in events:
        if e["kind"] == "activity" and _day(e["created_at"]) in acc: acc[_day(e["created_at"])].append(e["value"])
    trend = [{"day": d, "mean": round(sum(v) / len(v), 1) if v else None, "n": len(v)} for d, v in acc.items()]
    # behavioural anomalies: activity far below the personal baseline today, or a check-in missed today
    anomalies = []
    todays = {}
    for e in events:
        if e["kind"] == "activity" and _day(e["created_at"]) == today: todays.setdefault(e["elderly_id"], []).append(e["value"])
    for p in people:
        v = todays.get(p["id"])
        if v and p.get("baseline"):
            ratio = (sum(v) / len(v)) / p["baseline"]
            if ratio < ACTIVITY_DROP: anomalies.append({"elderly_id": p["id"], "name": p["name"], "kind": "activity_drop", "ratio": round(ratio, 2)})
    for c in missed: anomalies.append({"elderly_id": c["elderly_id"], "name": name.get(c["elderly_id"], "?"), "kind": "missed_checkin", "ratio": None})
    recent = sorted(events, key=lambda e: e["created_at"], reverse=True)[:10]
    # caregiver activity over the last 7 days
    cut = now - timedelta(days=7); cg = []
    for c in caregivers:
        mine = {p["id"] for p in people if p.get("caregiver_id") == c["id"]}; ma = [a for a in alerts if a["elderly_id"] in mine]
        done = [a for a in ma if a["resolved_by"] == "caregiver" and a["resolved_at"] and a["resolved_at"] >= cut]
        rts = [(a["resolved_at"] - a["created_at"]).total_seconds() / 60 for a in done]
        cg.append({"id": c["id"], "username": c["username"], "people": len(mine), "open_alerts": sum(a["status"] == "open" for a in ma),
                   "resolved_7d": len(done), "avg_response_min": round(sum(rts) / len(rts), 1) if rts else None})
    return {"totals": {"people": len(people), "caregivers": len(caregivers)}, "safety": {"status": status, "levels": levels},
            "alerts": {"open": len(open_a), "high_or_critical_open": len(crit_open), "acknowledged": len(ack_a), "per_day": per_day},
            "checkins_today": {"due": len(due), "answered": len(answered), "missed": len(missed), "pending": len(due) - len(answered) - len(missed)},
            "falls": {"today": fall_day.get(today, 0), "last_7_days": sum(fall_day.values()), "per_day": fall_day},
            "activity_trend": trend, "anomalies": anomalies,
            "recent_events": [{"id": e["id"], "elderly_id": e["elderly_id"], "name": name.get(e["elderly_id"], "?"), "kind": e["kind"], "value": e["value"], "at": e["created_at"].isoformat()} for e in recent],
            "caregivers": cg}
