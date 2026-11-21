"""HTTP routes: alerts."""
from app import i18n
from app.i18n import tr
from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.db.models import Alert, Notification
from app.security import current_user, lang_of
from app.services.people import my_people, person
from app.services.risk_service import close_alerts

router = APIRouter()

@router.get("/alerts")
def alerts(db=Depends(get_db), u=Depends(current_user), lang: str = Depends(lang_of)):
    ppl = {e.id: e.name for e in my_people(db, u)}
    rows = db.query(Alert).filter(Alert.elderly_id.in_(list(ppl))).order_by(Alert.created_at.desc()).limit(50).all() if ppl else []
    return [{"id": a.id, "elderly_id": a.elderly_id, "name": ppl[a.elderly_id], "level": a.level,
             "reasons": i18n.reasons_text(a.reasons, lang),
             "status": a.status, "stage": a.stage, "stage_text": tr(f"stage.{a.stage}", lang), "resolved_by": a.resolved_by,
             "created_at": a.created_at.isoformat()} for a in rows]

@router.post("/alerts/{aid}/ack")
def ack(aid: int, db=Depends(get_db), u=Depends(current_user)):
    a = db.get(Alert, aid)
    if not a: raise HTTPException(404, "Alert not found")
    e = person(db, u, a.elderly_id); close_alerts(db, e, "caregiver"); db.commit(); return {"ok": True}

@router.get("/notifications")
def notifications(db=Depends(get_db), u=Depends(current_user), lang: str = Depends(lang_of)):
    q = db.query(Notification) if u.role == "admin" else db.query(Notification).filter_by(user_id=u.id)
    return [{"id": n.id, "text": i18n.render_notification(n.text, lang), "at": n.created_at.isoformat()}
            for n in q.order_by(Notification.id.desc()).limit(30)]
