"""HTTP routes: careplan."""
from fastapi import APIRouter, Depends, HTTPException
from app.db.database import get_db, now
from app.db.models import CarePlanItem
from app.schemas import NewItem
from app.security import current_user
from app.services.care import item_for, item_out
from app.services.people import person

router = APIRouter()

@router.get("/elderly/{eid}/careplan")
def get_plan(eid: int, db=Depends(get_db), u=Depends(current_user)):
    person(db, u, eid); return [item_out(i) for i in db.query(CarePlanItem).filter_by(elderly_id=eid).order_by(CarePlanItem.time)]

@router.post("/elderly/{eid}/careplan")
def add_item(eid: int, b: NewItem, db=Depends(get_db), u=Depends(current_user)):
    person(db, u, eid)
    if b.kind not in ("medication", "meal", "water", "activity"): raise HTTPException(400, "Invalid kind")
    db.add(CarePlanItem(elderly_id=eid, **b.model_dump())); db.commit(); return {"ok": True}

@router.post("/careplan/{iid}/done")
def mark_done(iid: int, db=Depends(get_db), u=Depends(current_user)):
    i = item_for(db, u, iid); today = now().strftime("%Y-%m-%d")
    i.done_date = None if i.done_date == today else today; db.commit(); return item_out(i)

@router.delete("/careplan/{iid}")
def delete_item(iid: int, db=Depends(get_db), u=Depends(current_user)):
    db.delete(item_for(db, u, iid)); db.commit(); return {"ok": True}
