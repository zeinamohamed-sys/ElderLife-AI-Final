"""HTTP routes: elder self."""
from app import i18n
from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db, now
from app.db.models import Alert, CarePlanItem, CheckIn, Event
from app.notifications import notify
from app.security import elder_auth
from app.services.care import do_checkin, do_checkin_if_due, item_out
from app.services.risk_service import close_alerts, signals

router = APIRouter()

@router.get("/elder/me")
def elder_me(e=Depends(elder_auth), db=Depends(get_db)):
    s = signals(db, e); ci = db.query(CheckIn).filter_by(elderly_id=e.id).order_by(CheckIn.scheduled_at.desc()).first()
    open_alert = db.query(Alert).filter_by(elderly_id=e.id, status="open").first()
    return {"name": e.name, "checkin_due": bool(ci and not ci.responded_at),
            "prompt": bool(open_alert) or (s["fall"] and not s["fall_answered"]),
            "plan": [item_out(i) for i in db.query(CarePlanItem).filter_by(elderly_id=e.id).order_by(CarePlanItem.time)]}

@router.post("/elder/checkin")
def elder_checkin(e=Depends(elder_auth), db=Depends(get_db)):
    do_checkin(db, e.id); return {"ok": True}

@router.post("/elder/ok")
def elder_ok(e=Depends(elder_auth), db=Depends(get_db)):
    db.add(Event(elderly_id=e.id, kind="ok")); close_alerts(db, e, "person"); do_checkin_if_due(db, e.id); db.commit()
    return {"ok": True}

@router.post("/elder/help")
def elder_help(e=Depends(elder_auth), db=Depends(get_db)):
    db.add(Event(elderly_id=e.id, kind="sos"))
    a = db.query(Alert).filter_by(elderly_id=e.id, status="open").first()
    if not a:
        a = Alert(elderly_id=e.id, level="Critical", stage=1,
                  reasons=i18n.reasons_to_json([{"key": "reason.sos", "params": {}}])); db.add(a); db.flush()
    a.level = "Critical"
    if a.stage < 3: a.stage = 3; db.commit(); notify(db, a)
    db.commit(); return {"ok": True}

@router.post("/elder/done/{iid}")
def elder_done(iid: int, e=Depends(elder_auth), db=Depends(get_db)):
    i = db.get(CarePlanItem, iid)
    if not i or i.elderly_id != e.id: raise HTTPException(404, "Item not found")
    today = now().strftime("%Y-%m-%d"); i.done_date = None if i.done_date == today else today; db.commit()
    return item_out(i)
