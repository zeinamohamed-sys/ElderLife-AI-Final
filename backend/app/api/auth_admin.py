"""HTTP routes: auth admin."""
import hmac
import os
from app import i18n
from app.mlmodels import load_json
from app.risk import ml_enabled
from app.vision import POSE_MODELS
from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db
from app.db.models import Elderly, User
from app.schemas import Assign, LangIn, Login, NewUser
from app.core.logging_config import log
from app.services.throttle import throttle
from app.security import admin_only, current_user, hash_pw, make_token, new_user

router = APIRouter()

@router.get("/model/info")
def model_info(_=Depends(current_user)):
    """Which AI models are active and how they scored on the (synthetic) evaluation."""
    return {"risk_model_active": ml_enabled(), "pose_model_active": bool(POSE_MODELS) and os.getenv("ML_MODE", "auto") != "off",
            "metrics": load_json("metrics.json")}

@router.get("/health")
def health(): return {"status": "ok"}

@router.post("/auth/login")
def login(b: Login, db=Depends(get_db)):
    wait = throttle.blocked_for(b.username)
    if wait: raise HTTPException(429, f"Too many wrong passwords. Try again in {wait} seconds")
    u = db.query(User).filter_by(username=b.username).first()
    if not u or not hmac.compare_digest(u.pw, hash_pw(b.password, u.salt)):
        throttle.failed(b.username); log.warning("failed login for username=%r", b.username[:64]); raise HTTPException(401, "Wrong username or password")
    throttle.ok(b.username)
    return {"token": make_token(u.id), "user": {"id": u.id, "username": u.username, "role": u.role, "lang": u.lang or i18n.DEFAULT_LANG}}

@router.get("/auth/me")
def me(u=Depends(current_user)): return {"id": u.id, "username": u.username, "role": u.role, "lang": u.lang or i18n.DEFAULT_LANG}

@router.get("/languages")
def languages(): return {"languages": list(i18n.SUPPORTED), "names": i18n.LANG_NAMES, "default": i18n.DEFAULT_LANG}

@router.put("/auth/lang")
def set_lang(b: LangIn, db=Depends(get_db), u=Depends(current_user)):
    """Language of the email/Telegram alerts this user receives (the screen language is chosen in Settings)."""
    if b.lang not in i18n.SUPPORTED: raise HTTPException(400, "Unsupported language")
    u.lang = b.lang; db.commit(); return {"ok": True, "lang": u.lang}

@router.post("/users")
def create_user(b: NewUser, db=Depends(get_db), _=Depends(admin_only)):
    if len(b.password) < 6: raise HTTPException(400, "Password must be at least 6 characters")
    if db.query(User).filter_by(username=b.username).first(): raise HTTPException(400, "Username already exists")
    return {"id": new_user(db, b.username, b.password, "caregiver", b.telegram_chat_id, b.email).id}

@router.get("/users")
def users(db=Depends(get_db), _=Depends(admin_only)):
    return [{"id": x.id, "username": x.username, "role": x.role, "email": x.email} for x in db.query(User)]

@router.get("/admin/people")
def admin_people(db=Depends(get_db), _=Depends(admin_only)):
    return [{"id": e.id, "name": e.name, "age": e.age, "caregiver_id": e.caregiver_id, "access_code": e.access_code} for e in db.query(Elderly)]

@router.put("/elderly/{eid}/assign")
def assign(eid: int, b: Assign, db=Depends(get_db), _=Depends(admin_only)):
    e = db.get(Elderly, eid)
    if not e: raise HTTPException(404, "Person not found")
    if b.caregiver_id and not db.get(User, b.caregiver_id): raise HTTPException(400, "Caregiver not found")
    e.caregiver_id = b.caregiver_id; db.commit(); return {"ok": True}
