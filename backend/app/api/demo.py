"""HTTP routes: demo."""
import random
from app import i18n
from app.i18n import tr
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import PROD
from app.db.database import get_db, now
from app.db.models import Alert, CarePlanItem, CheckIn, Elderly, Event, Notification, RiskLog, User
from app.security import admin_only, lang_of, new_user
from app.services.people import new_code
from app.services.risk_service import evaluate
from app.services.scheduler import tick

router = APIRouter()

@router.post("/simulate/seed")
def seed(db=Depends(get_db), _=Depends(admin_only), lang: str = Depends(lang_of)):
    """Synthetic demo data (not real people). The care-plan reminders are created in your language."""
    if PROD: raise HTTPException(403, "Demo data is disabled in production")
    for m in (Notification, RiskLog, Alert, Event, CheckIn, CarePlanItem, Elderly): db.query(m).delete()
    cgs = [db.query(User).filter_by(username=n).first() or new_user(db, n, "care123") for n in ("sara", "omar")]
    names = ["Hoda Mahmoud", "Samir Fathy", "Nadia Ibrahim", "Abdel Rahman Ali", "Layla Hassan", "Mostafa Kamel",
             "Fatma Zaki", "Youssef Adel", "Salwa Naguib", "Ahmed Sherif", "Mona Said", "Kamal Aboud"]
    t = now(); today = t.strftime("%Y-%m-%d")
    for n in names:
        e = Elderly(name=n, age=random.randint(68, 90), caregiver_id=random.choice(cgs).id,
                    emergency_contact=tr("seed.contact", lang), access_code=new_code(db))
        db.add(e); db.flush()
        for kind, key, tm in [("medication", "seed.medication", "08:00"), ("meal", "seed.meal", "09:30"),
                              ("water", "seed.water", "11:00"), ("activity", "seed.activity", "17:00")]:
            db.add(CarePlanItem(elderly_id=e.id, kind=kind, title=tr(key, lang), time=tm))
        sc = random.choices(["ok", "late", "inactive", "fall"], [6, 2, 2, 2])[0]
        if sc == "ok":
            for it in db.query(CarePlanItem).filter_by(elderly_id=e.id): it.done_date = today
        for d in range(1, 8):  # a week of normal check-ins (builds the usual check-in delay)
            s = (t - timedelta(days=d)).replace(hour=9, minute=0, second=0, microsecond=0)
            db.add(CheckIn(elderly_id=e.id, scheduled_at=s, responded_at=s + timedelta(minutes=random.randint(3, 20))))
        sched = t - timedelta(minutes=60 if sc == "ok" else 180)
        db.add(CheckIn(elderly_id=e.id, scheduled_at=sched, responded_at=sched + timedelta(minutes=8) if sc == "ok" else None))
        for i in range(8):  # normal history (builds the personal baseline)
            db.add(Event(elderly_id=e.id, kind="activity", value=random.uniform(40, 60), created_at=t - timedelta(hours=random.randint(5, 70))))
        for i in range(6):
            v = random.uniform(40, 60) if sc in ("ok", "late") else random.uniform(5, 20)
            db.add(Event(elderly_id=e.id, kind="activity", value=v, created_at=t - timedelta(minutes=25 * i + 5)))
        if sc == "fall": db.add(Event(elderly_id=e.id, kind="fall", value=0.9, created_at=t - timedelta(minutes=10)))
        if random.random() < .5:  # older falls (for the "falls by hour" chart)
            hr = random.choice([2, 3, 4, 5, 6, 21, 22, 23, 9, 14])
            db.add(Event(elderly_id=e.id, kind="fall", value=0.9, created_at=(t - timedelta(days=random.randint(2, 6))).replace(hour=hr)))
        if random.random() < .6:  # past alerts for the analytics page
            c = t - timedelta(days=random.randint(1, 6), hours=random.randint(0, 5))
            db.add(Alert(elderly_id=e.id, level="High", reasons=i18n.reasons_to_json([{"key": "reason.fall_detected", "params": {}}]),
                         status="resolved", stage=3, created_at=c,
                         resolved_by=random.choice(["person", "person", "caregiver"]), resolved_at=c + timedelta(minutes=random.randint(2, 15))))
    db.commit()
    for e in db.query(Elderly).all(): evaluate(db, e)
    tick(db, True)
    return {"seeded": len(names), "caregivers": ["sara / care123", "omar / care123"]}
