"""HTTP routes: analytics."""
import csv
import io
from app import i18n
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from app.db.database import get_db, now
from app.db.models import Alert, CarePlanItem, CheckIn, Event, RiskLog
from app.security import current_user, export_auth
from app.services.people import my_people

router = APIRouter()

@router.get("/analytics")
def analytics(db=Depends(get_db), u=Depends(current_user)):
    ids = [e.id for e in my_people(db, u)]
    als = db.query(Alert).filter(Alert.elderly_id.in_(ids)).all() if ids else []
    evs = db.query(Event).filter(Event.elderly_id.in_(ids)).all() if ids else []
    days = {(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(6, -1, -1)}
    for a in als:
        d = a.created_at.strftime("%Y-%m-%d")
        if d in days: days[d] += 1
    by_hour = [0] * 24
    for x in evs:
        if x.kind == "fall": by_hour[x.created_at.hour] += 1
    rts = [(a.resolved_at - a.created_at).total_seconds() / 60 for a in als if a.resolved_at]
    self_res = sum(a.resolved_by == "person" for a in als)
    late = db.query(CheckIn).filter(CheckIn.elderly_id.in_(ids), CheckIn.responded_at == None, CheckIn.scheduled_at < now() - timedelta(minutes=30)).count() if ids else 0
    return {"alerts_per_day": days, "avg_response_min": round(sum(rts) / len(rts), 1) if rts else None,
            "falls": sum(x.kind == "fall" for x in evs), "checkin_failures": late, "total_alerts": len(als),
            "self_resolved": self_res, "false_alarm_rate": round(100 * self_res / len(als)) if als else None, "falls_by_hour": by_hour}

@router.get("/export/{name}")
def export(name: str, db=Depends(get_db), u=Depends(export_auth)):
    ids = [e.id for e in my_people(db, u)]; buf = io.StringIO(); w = csv.writer(buf)
    def ins(col): return col.in_(ids)
    if name == "alerts":
        w.writerow(["id", "elderly_id", "level", "reasons", "status", "stage", "resolved_by", "created_at", "resolved_at"])
        for a in db.query(Alert).filter(ins(Alert.elderly_id)): w.writerow([a.id, a.elderly_id, a.level, i18n.reasons_text(a.reasons, "en"), a.status, a.stage, a.resolved_by, a.created_at, a.resolved_at])
    elif name == "risk":
        w.writerow(["elderly_id", "level", "score", "created_at"])
        for r in db.query(RiskLog).filter(ins(RiskLog.elderly_id)): w.writerow([r.elderly_id, r.level, r.score, r.created_at])
    elif name == "events":
        w.writerow(["id", "elderly_id", "kind", "value", "created_at"])
        for x in db.query(Event).filter(ins(Event.elderly_id)): w.writerow([x.id, x.elderly_id, x.kind, x.value, x.created_at])
    elif name == "checkins":
        w.writerow(["id", "elderly_id", "scheduled_at", "responded_at"])
        for c in db.query(CheckIn).filter(ins(CheckIn.elderly_id)): w.writerow([c.id, c.elderly_id, c.scheduled_at, c.responded_at])
    elif name == "careplan":
        w.writerow(["id", "elderly_id", "kind", "title", "time", "done_date"])
        for i in db.query(CarePlanItem).filter(ins(CarePlanItem.elderly_id)): w.writerow([i.id, i.elderly_id, i.kind, i.title, i.time, i.done_date])
    elif name == "people":  # no names, contacts or access codes
        w.writerow(["elderly_id", "age", "baseline_activity", "checkin_time", "caregiver_id"])
        for e in my_people(db, u): w.writerow([e.id, e.age, e.baseline_activity, e.checkin_time, e.caregiver_id])
    else: raise HTTPException(404, "Use alerts, risk, events, checkins, careplan or people")
    return Response(buf.getvalue(), media_type="text/csv")
