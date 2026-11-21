"""Which people a user may see; access codes."""
import random
from fastapi import HTTPException
from app.db.models import Elderly

def my_people(db, u):
    q = db.query(Elderly); return q if u.role == "admin" else q.filter(Elderly.caregiver_id == u.id)

def person(db, u, eid):
    e = my_people(db, u).filter(Elderly.id == eid).first()
    if not e: raise HTTPException(404, "Person not found")
    return e

def target_person(db, u, eid):  # u is None for trusted devices (camera / AI service)
    if u: return person(db, u, eid)
    e = db.get(Elderly, eid)
    if not e: raise HTTPException(404, "Person not found")
    return e

def new_code(db):
    while True:
        c = f"{random.randint(100000, 999999)}"
        if not db.query(Elderly).filter_by(access_code=c).first(): return c
