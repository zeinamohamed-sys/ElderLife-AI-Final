"""HTTP routes: dashboard summary and the cross-person lists used by the Events, Check-ins and Care plan pages."""
from fastapi import APIRouter, Depends, HTTPException
from datetime import timedelta
from app.db.database import get_db, now
from app.db.models import Alert, CarePlanItem, CheckIn, Event, User
from app.security import current_user
from app.services.care import item_out
from app.services.dashboard import build_summary
from app.services.people import my_people
from app.services.risk_service import evaluate

router = APIRouter()

def _ids(db, u): return [e.id for e in my_people(db, u).all()]

@router.get("/dashboard/summary")
def dashboard_summary(db=Depends(get_db), u=Depends(current_user)):
    """Everything the main dashboard shows, scoped to the people this user may see (admins: everyone)."""
    people = []
    for e in my_people(db, u).all():
        r = evaluate(db, e); people.append({"id": e.id, "name": e.name, "level": r["level"], "score": r["score"], "baseline": e.baseline_activity, "caregiver_id": e.caregiver_id})
    ids = [p["id"] for p in people]; since = now() - timedelta(days=15)
    alerts = [{"id": a.id, "elderly_id": a.elderly_id, "level": a.level, "status": a.status, "created_at": a.created_at, "resolved_at": a.resolved_at, "resolved_by": a.resolved_by}
              for a in (db.query(Alert).filter(Alert.elderly_id.in_(ids), Alert.created_at >= since).all() if ids else [])]
    events = [{"id": x.id, "elderly_id": x.elderly_id, "kind": x.kind, "value": x.value or 0, "created_at": x.created_at}
              for x in (db.query(Event).filter(Event.elderly_id.in_(ids), Event.created_at >= since).all() if ids else [])]
    checkins = [{"elderly_id": c.elderly_id, "scheduled_at": c.scheduled_at, "responded_at": c.responded_at}
                for c in (db.query(CheckIn).filter(CheckIn.elderly_id.in_(ids), CheckIn.scheduled_at >= since).all() if ids else [])]
    cgs = db.query(User).filter_by(role="caregiver").all() if u.role == "admin" else [u]
    return build_summary(people, alerts, events, checkins, [{"id": c.id, "username": c.username} for c in cgs], now())

@router.get("/events")
def list_events(elderly_id: int | None = None, kind: str | None = None, limit: int = 100, db=Depends(get_db), u=Depends(current_user)):
    """Recent events across my people, newest first (filter by person and/or kind)."""
    if kind is not None and kind not in ("activity", "fall", "ok", "sos"): raise HTTPException(400, "kind must be activity, fall, ok or sos")
    ids = _ids(db, u)
    if elderly_id is not None:
        if elderly_id not in ids: raise HTTPException(404, "Person not found")
        ids = [elderly_id]
    if not ids: return []
    names = {e.id: e.name for e in my_people(db, u).all()}
    q = db.query(Event).filter(Event.elderly_id.in_(ids))
    if kind: q = q.filter(Event.kind == kind)
    return [{"id": x.id, "elderly_id": x.elderly_id, "name": names.get(x.elderly_id), "kind": x.kind, "value": x.value, "at": x.created_at.isoformat()}
            for x in q.order_by(Event.created_at.desc()).limit(max(1, min(limit, 500))).all()]

@router.get("/checkins")
def list_checkins(elderly_id: int | None = None, status: str | None = None, limit: int = 100, db=Depends(get_db), u=Depends(current_user)):
    """Check-ins across my people, newest first. status: answered | missed (unanswered and over 30 minutes late) | pending."""
    if status is not None and status not in ("answered", "missed", "pending"): raise HTTPException(400, "status must be answered, missed or pending")
    ids = _ids(db, u)
    if elderly_id is not None:
        if elderly_id not in ids: raise HTTPException(404, "Person not found")
        ids = [elderly_id]
    if not ids: return []
    names = {e.id: e.name for e in my_people(db, u).all()}; late = now() - timedelta(minutes=30); out = []
    for c in db.query(CheckIn).filter(CheckIn.elderly_id.in_(ids)).order_by(CheckIn.scheduled_at.desc()).limit(max(1, min(limit, 500))).all():
        st = "answered" if c.responded_at else "missed" if c.scheduled_at < late else "pending"
        if status and st != status: continue
        out.append({"id": c.id, "elderly_id": c.elderly_id, "name": names.get(c.elderly_id), "status": st, "scheduled_at": c.scheduled_at.isoformat(), "responded_at": c.responded_at.isoformat() if c.responded_at else None})
    return out

@router.get("/careplan")
def list_careplan(db=Depends(get_db), u=Depends(current_user)):
    """All care-plan items of my people (recorded reminders only), grouped by person."""
    people = my_people(db, u).all(); out = []
    for e in people:
        items = db.query(CarePlanItem).filter_by(elderly_id=e.id).order_by(CarePlanItem.time).all()
        out.append({"elderly_id": e.id, "name": e.name, "items": [item_out(i) for i in items]})
    return out
