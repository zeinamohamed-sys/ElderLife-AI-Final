"""HTTP routes: elderly."""
from app import i18n
from fastapi import APIRouter, Depends
from app.db.database import get_db, now
from app.db.models import CheckIn, Elderly, Event, RiskLog
from app.schemas import NewElderly
from app.security import current_user, lang_of
from app.services.care import do_checkin, localize_risk
from app.services.people import my_people, new_code, person
from app.services.risk_service import evaluate

router = APIRouter()

@router.get("/elderly")
def list_elderly(db=Depends(get_db), u=Depends(current_user), lang: str = Depends(lang_of)):
    out = []
    for e in my_people(db, u).all():
        r = evaluate(db, e)
        out.append({"id": e.id, "name": e.name, "age": e.age, "level": r["level"], "score": r["score"],
                    "reasons": i18n.reasons_list(r["reason_codes"], lang)})
    return sorted(out, key=lambda x: -x["score"])

@router.post("/elderly")
def create_elderly(b: NewElderly, db=Depends(get_db), u=Depends(current_user)):
    d = b.model_dump()
    if u.role != "admin": d["caregiver_id"] = u.id
    e = Elderly(**d, access_code=new_code(db)); db.add(e); db.flush()
    db.add(CheckIn(elderly_id=e.id, scheduled_at=now())); db.commit()
    return {"id": e.id, "access_code": e.access_code}

@router.get("/elderly/{eid}")
def get_elderly(eid: int, db=Depends(get_db), u=Depends(current_user), lang: str = Depends(lang_of)):
    e = person(db, u, eid)
    ev = db.query(Event).filter_by(elderly_id=eid).order_by(Event.created_at.desc()).limit(10).all()
    hist = db.query(RiskLog).filter_by(elderly_id=eid).order_by(RiskLog.id.desc()).limit(10).all()
    return {"id": e.id, "name": e.name, "age": e.age, "baseline_activity": e.baseline_activity, "access_code": e.access_code,
            "risk": localize_risk(evaluate(db, e), lang),
            "events": [{"kind": x.kind, "value": x.value, "at": x.created_at.isoformat()} for x in ev],
            "history": [{"level": x.level, "score": x.score, "at": x.created_at.isoformat()} for x in hist]}

@router.post("/elderly/{eid}/checkin")
def checkin(eid: int, db=Depends(get_db), u=Depends(current_user)):
    person(db, u, eid); do_checkin(db, eid); return {"ok": True}

@router.get("/elderly/{eid}/timeline")
def timeline(eid: int, limit: int = 30, db=Depends(get_db), u=Depends(current_user)):
    """Recent events (activity/fall/ok/sos) and check-ins of one person, newest first. Same access rule as GET /elderly/{id}."""
    e = person(db, u, eid); limit = max(1, min(limit, 200))
    ev = db.query(Event).filter_by(elderly_id=e.id).order_by(Event.created_at.desc()).limit(limit).all()
    ci = db.query(CheckIn).filter_by(elderly_id=e.id).order_by(CheckIn.scheduled_at.desc()).limit(limit).all()
    return {"events": [{"id": x.id, "kind": x.kind, "value": x.value, "at": x.created_at.isoformat()} for x in ev],
            "checkins": [{"id": x.id, "scheduled_at": x.scheduled_at.isoformat(), "responded_at": x.responded_at.isoformat() if x.responded_at else None} for x in ci]}
