"""HTTP routes: wearable accelerometer fall detection (complements /vision/pose)."""
from fastapi import APIRouter, Depends, HTTPException
from app import accel_model
from app.db.database import get_db
from app.db.models import Event
from app.schemas import AccelWindow
from app.security import current_user, ingest_auth
from app.services.people import target_person
from app.services.risk_service import evaluate

router = APIRouter()

@router.get("/sensor/accel/model")
def accel_model_info(u=Depends(current_user)):
    """Whether a usable accelerometer model is loaded, and what data it was trained on."""
    return accel_model.info()

@router.post("/sensor/accel")
def sensor_accel(b: AccelWindow, db=Depends(get_db), u=Depends(ingest_auth)):
    """A 3 s window of accelerometer samples (50 Hz, in g). A predicted fall becomes a 'fall' event (value = probability) and goes through the normal verify-then-escalate flow."""
    e = target_person(db, u, b.elderly_id)
    if b.fs != accel_model.FS_EXPECTED: raise HTTPException(400, f"fs must be {accel_model.FS_EXPECTED} Hz (resample on the device)")
    err = accel_model.check_window(b.window)
    if err: raise HTTPException(400, err)
    res = accel_model.predict_window(b.window)
    if res is None: raise HTTPException(503, f"No accelerometer model available: {accel_model.info()['reason']}")
    if res["fall"]: db.add(Event(elderly_id=e.id, kind="fall", value=res["probability"])); db.commit()
    return {**res, "risk": evaluate(db, e)}
