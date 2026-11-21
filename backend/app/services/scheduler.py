"""Background loop: escalation, daily check-ins, baselines."""
import os
import threading
import time
from contextlib import asynccontextmanager
from datetime import timedelta
from app.core.config import STEP
from app.core.logging_config import log
from app.db.database import SessionLocal, now
from app.db.models import Alert, CheckIn, Elderly, Event, User
from app.notifications import notify
from app.security import new_user

def tick(db, update_baselines=False):
    t = now()
    for a in db.query(Alert).filter_by(status="open").all():
        target = min(4, 1 + int((t - a.created_at).total_seconds() // STEP))
        while a.stage < target:
            a.stage += 1
            if a.stage >= 3: notify(db, a)
    midnight = t.replace(hour=0, minute=0, second=0, microsecond=0)
    for e in db.query(Elderly).all():
        h, m = map(int, e.checkin_time.split(":")); sched = t.replace(hour=h, minute=m, second=0, microsecond=0)
        if t >= sched and not db.query(CheckIn).filter(CheckIn.elderly_id == e.id, CheckIn.scheduled_at >= midnight).first():
            db.add(CheckIn(elderly_id=e.id, scheduled_at=sched))
        if update_baselines:  # personal baseline = mean activity of older history (not the last 3 hours)
            old = [x.value for x in db.query(Event).filter(Event.elderly_id == e.id, Event.kind == "activity",
                   Event.created_at < t - timedelta(hours=3), Event.created_at > t - timedelta(days=7))]
            if len(old) >= 5: e.baseline_activity = round(sum(old) / len(old), 1)
    db.commit()

@asynccontextmanager
async def lifespan(app):
    db = SessionLocal()
    if not db.query(User).first():   # first start: create the admin (demo password only outside production)
        new_user(db, os.getenv("ADMIN_USERNAME", "admin"), os.getenv("ADMIN_PASSWORD", "admin123"), "admin")
    db.close()
    def loop():
        n = 0
        while True:
            try:
                d = SessionLocal(); tick(d, n % 6 == 0); d.close()
            except Exception: log.exception("background tick failed")
            n += 1; time.sleep(10)
    threading.Thread(target=loop, daemon=True).start()
    yield
