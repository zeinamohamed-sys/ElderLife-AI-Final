"""HTTP routes: events."""
from app.vision import ACTIVITY_LEVEL, POINTS, classify_auto
from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.db.models import Event
from app.schemas import NewEvent, Pose
from app.security import ingest_auth
from app.services.people import target_person
from app.services.risk_service import close_alerts, evaluate

router = APIRouter()

@router.post("/events")
def add_event(b: NewEvent, db=Depends(get_db), u=Depends(ingest_auth)):
    if b.kind not in ("activity", "fall", "ok", "sos"): raise HTTPException(400, "kind must be activity, fall, ok or sos")
    e = target_person(db, u, b.elderly_id)
    db.add(Event(**b.model_dump()))
    if b.kind == "ok": close_alerts(db, e, "person")
    db.commit(); return evaluate(db, e)

@router.post("/vision/pose")
def vision_pose(b: Pose, db=Depends(get_db), u=Depends(ingest_auth)):
    """Camera/CV service sends body keypoints only (never images). Returns the recognised activity."""
    e = target_person(db, u, b.elderly_id)
    missing = [p for p in POINTS if p not in b.keypoints]
    if missing: raise HTTPException(400, f"Missing keypoints: {', '.join(missing)}")
    act, conf, source = classify_auto(b.keypoints, b.prev_keypoints, b.dt_s)
    db.add(Event(elderly_id=e.id, kind="activity", value=ACTIVITY_LEVEL[act]))
    if act == "falling": db.add(Event(elderly_id=e.id, kind="fall", value=conf))
    db.commit(); return {"activity": act, "confidence": conf, "source": source, "risk": evaluate(db, e)}
