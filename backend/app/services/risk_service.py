"""Risk signals, evaluation and alert closing."""
from app import i18n
from app.risk import NEXT_STEP, assess
from datetime import datetime, timedelta
from app.core.logging_config import log
from app.core.config import FALL_MIN_CONF, SNOOZE_MIN, VERIFY_S
from app.db.database import now
from app.db.models import Alert, CarePlanItem, CheckIn, Event, RiskLog

def is_overdue(i, grace=30):
    t = datetime.now()
    if i.done_date == t.strftime("%Y-%m-%d"): return False
    h, m = map(int, i.time.split(":"))
    return t > t.replace(hour=h, minute=m, second=0, microsecond=0) + timedelta(minutes=grace)

def signals(db, e):
    t = now()
    ci = db.query(CheckIn).filter_by(elderly_id=e.id).order_by(CheckIn.scheduled_at.desc()).first()
    delay = max(0, ((ci.responded_at or t) - ci.scheduled_at).total_seconds() / 60) if ci else 0
    past = [c for c in db.query(CheckIn).filter(CheckIn.elderly_id == e.id, CheckIn.responded_at != None)
            .order_by(CheckIn.scheduled_at.desc()).limit(8).all() if not ci or c.id != ci.id]
    ds = sorted((c.responded_at - c.scheduled_at).total_seconds() / 60 for c in past)
    usual = ds[len(ds) // 2] if len(ds) >= 3 else None      # the person's usual check-in delay (median)
    acts = [x.value for x in db.query(Event).filter(Event.elderly_id == e.id, Event.kind == "activity", Event.created_at > t - timedelta(hours=3))]
    ratio = (sum(acts) / len(acts)) / e.baseline_activity if acts else None
    falls = [x for x in db.query(Event).filter(Event.elderly_id == e.id, Event.kind == "fall", Event.created_at > t - timedelta(hours=2))
             .order_by(Event.created_at.desc()) if (x.value or 1.0) >= FALL_MIN_CONF]   # low-confidence falls are ignored
    fall = falls[0] if falls else None
    answered = bool(fall and db.query(Event).filter(Event.elderly_id == e.id, Event.kind == "ok", Event.created_at > fall.created_at).first())
    sos = db.query(Event).filter(Event.elderly_id == e.id, Event.kind == "sos", Event.created_at > t - timedelta(hours=1)).order_by(Event.created_at.desc()).first()
    sos_on = bool(sos and not db.query(Event).filter(Event.elderly_id == e.id, Event.kind == "ok", Event.created_at > sos.created_at).first())
    missed = sum(is_overdue(i) for i in db.query(CarePlanItem).filter_by(elderly_id=e.id))
    return {"checkin_delay_min": round(delay), "checkin_responded": bool(ci and ci.responded_at),
            "checkin_usual_min": round(usual) if usual is not None else None, "activity_ratio": ratio,
            "fall": bool(fall), "fall_answered": answered, "fall_age_s": (t - fall.created_at).total_seconds() if fall else 0,
            "verify_s": VERIFY_S, "sos": sos_on, "missed_reminders": missed,
            "fall_conf": ((fall.value or 1.0) if fall else 0.0), "age": e.age or 78, "hour": t.hour}

def snoozed(db, e):
    if not (e.silenced_until and now() < e.silenced_until): return False
    return not db.query(Event).filter(Event.elderly_id == e.id, Event.kind.in_(["fall", "sos"]), Event.created_at > e.silenced_at).first()

def evaluate(db, e):
    s = signals(db, e); r = assess(s)
    last = db.query(RiskLog).filter_by(elderly_id=e.id).order_by(RiskLog.id.desc()).first()
    if not last or last.level != r["level"]:
        db.add(RiskLog(elderly_id=e.id, level=r["level"], score=r["score"])); db.commit()
    if r["level"] in ("High", "Critical"):
        reasons = i18n.reasons_to_json(r["reason_codes"])   # stored as keys, translated when read
        a = db.query(Alert).filter_by(elderly_id=e.id, status="open").first()
        if a: a.level, a.reasons = r["level"], reasons
        elif not snoozed(db, e):
            db.add(Alert(elderly_id=e.id, level=r["level"], reasons=reasons, stage=1))
            log.info("alert opened elderly_id=%s level=%s score=%s", e.id, r["level"], r["score"])
        db.commit()
    return {**r, "next_step": NEXT_STEP.get(r["level"]), "signals": s}

def close_alerts(db, e, by):  # by: "person" (answered "I'm OK") or "caregiver" (acknowledged)
    for a in db.query(Alert).filter_by(elderly_id=e.id, status="open").all():
        a.status = "resolved" if by == "person" else "acknowledged"; a.resolved_at = now(); a.resolved_by = by
    e.silenced_at = now(); e.silenced_until = now() + timedelta(minutes=SNOOZE_MIN)
