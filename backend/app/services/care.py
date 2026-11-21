"""Helpers shared by several routers."""
from app import i18n
from app.i18n import tr
from fastapi import HTTPException
from app.db.database import now
from app.db.models import CarePlanItem, CheckIn
from app.services.people import person
from app.services.risk_service import is_overdue

def localize_risk(r, lang):
    """Translate the reasons, the next step and the model factors for the reader."""
    out = {**r, "reasons": i18n.reasons_list(r["reason_codes"], lang),
           "next_step": tr("next." + r["level"].lower(), lang) if r["level"] in ("Medium", "High", "Critical") else None}
    if r.get("model"): out["model"] = {**r["model"], "top_factors": i18n.factor_texts(r["model"].get("top_factor_keys"), lang)}
    return out

def do_checkin(db, eid):
    ci = db.query(CheckIn).filter_by(elderly_id=eid, responded_at=None).order_by(CheckIn.scheduled_at.desc()).first()
    if not ci: ci = CheckIn(elderly_id=eid, scheduled_at=now()); db.add(ci)
    ci.responded_at = now(); db.commit()

def item_out(i):
    return {"id": i.id, "kind": i.kind, "title": i.title, "time": i.time, "note": i.note,
            "done_today": i.done_date == now().strftime("%Y-%m-%d"), "overdue": is_overdue(i)}

def item_for(db, u, iid):
    i = db.get(CarePlanItem, iid)
    if not i: raise HTTPException(404, "Item not found")
    person(db, u, i.elderly_id); return i

def do_checkin_if_due(db, eid):  # answering "I'm OK" also counts as today's check-in when one is waiting
    ci = db.query(CheckIn).filter_by(elderly_id=eid, responded_at=None).order_by(CheckIn.scheduled_at.desc()).first()
    if ci: ci.responded_at = now()
