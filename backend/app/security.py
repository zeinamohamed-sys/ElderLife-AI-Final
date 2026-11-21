"""Passwords, tokens and the FastAPI dependencies for authentication and roles."""
import base64
import hashlib
import hmac
import os
import time
from app import i18n
from fastapi import Depends, HTTPException, Header, Request
from types import SimpleNamespace
from app.core.config import DEVICE_KEY, EXPORT_KEY, SECRET
from app.db.database import get_db
from app.db.models import Elderly, User

def lang_of(request: Request) -> str:
    """The language this request wants, from Accept-Language (set by the frontend Settings screen)."""
    return i18n.negotiate(request.headers.get("accept-language"))

def hash_pw(pw, salt): return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()

def new_user(db, username, pw, role="caregiver", tg=None, email=None):
    salt = os.urandom(8).hex()
    u = User(username=username, salt=salt, pw=hash_pw(pw, salt), role=role, telegram_chat_id=tg, email=email)
    db.add(u); db.commit(); return u

def make_token(uid):
    p = f"{uid}:{int(time.time()) + 86400}"
    sig = hmac.new(SECRET.encode(), p.encode(), "sha256").hexdigest()
    return base64.urlsafe_b64encode(f"{p}:{sig}".encode()).decode()

def read_token(tok):
    try:
        uid, exp, sig = base64.urlsafe_b64decode(tok.encode()).decode().split(":")
        ok = hmac.compare_digest(sig, hmac.new(SECRET.encode(), f"{uid}:{exp}".encode(), "sha256").hexdigest())
        return int(uid) if ok and int(exp) > time.time() else None
    except Exception: return None

def current_user(authorization: str = Header(None), db=Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        uid = read_token(authorization[7:]); u = db.get(User, uid) if uid else None
        if u: return u
    raise HTTPException(401, "Please log in")

def ingest_auth(authorization: str = Header(None), x_device_key: str = Header(None), db=Depends(get_db)):
    return None if x_device_key and hmac.compare_digest(x_device_key, DEVICE_KEY) else current_user(authorization, db)

def admin_only(u=Depends(current_user)):
    if u.role != "admin": raise HTTPException(403, "Admins only")
    return u

def elder_auth(x_elder_code: str = Header(None), db=Depends(get_db)):
    e = db.query(Elderly).filter_by(access_code=x_elder_code).first() if x_elder_code else None
    if not e: raise HTTPException(401, "Wrong code")
    return e

def export_auth(authorization: str = Header(None), x_export_key: str = Header(None), db=Depends(get_db)):
    """CSV exports: a normal login, or the read-only EXPORT_KEY (for Power BI scheduled refresh, which cannot renew a 24 h token). The key sees all people but can do nothing else."""
    if EXPORT_KEY and x_export_key and hmac.compare_digest(x_export_key, EXPORT_KEY): return SimpleNamespace(id=0, role="admin", username="export-key")
    return current_user(authorization, db)
