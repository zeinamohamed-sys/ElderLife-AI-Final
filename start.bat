@echo off
title ElderLife AI - Rich Demo Launcher
echo [1/4] Starting Docker containers...
docker compose up -d

echo [2/4] Waiting for Backend to initialize...
timeout /t 8 /nobreak > nul

echo [3/4] Populating rich live demo dataset...
docker compose exec -T backend python -c "import random; from datetime import datetime, timedelta; from app.db.database import SessionLocal; from app.db.models import Elderly, Event, Alert, Checkin, User; from app.api.demo import seed; db = SessionLocal(); seed(db=db, lang='en') if not db.query(Elderly).first() else None; cg = db.query(User).filter(User.role=='caregiver').first() or db.query(User).first(); names = ['Ahmed Mahmoud','Fatma Hassan','Sayed Ibrahim','Nadia Kamel','Mahmoud Ali','Zeinab Omar','Hassan Taha','Samira Youssef','Gamal Adel','Hoda Mansour','Kamel Fouad','Amina Zaki','Tarek Nabil','Soad Salem','Mostafa Farid','Laila Shawky','Adel Ragab','Mona Helmy','Ibrahim Lotfy','Karima Anwar','Ezzat Galal','Nagwa Saber','Farouk Soliman','Wafaa Badr']; existing = {e.name for e in db.query(Elderly).all()}; new_people = [Elderly(name=n, age=random.randint(68,89), room=f'R-{100+i}', caregiver_id=cg.id if cg else None, access_code=f'ELDER{200+i}') for i,n in enumerate(names) if n not in existing]; db.add_all(new_people); db.commit(); all_p = db.query(Elderly).all(); now = datetime.utcnow(); [db.add(Event(elderly_id=random.choice(all_p).id, kind=random.choice(['fall','inactivity','activity','check_in']), source=random.choice(['vision_tcn','accel_sensor','manual']), score=round(random.uniform(0.65,0.98),2), created_at=now - timedelta(days=random.randint(0,13), hours=random.randint(0,23)))) for _ in range(90)]; [db.add(Alert(elderly_id=random.choice(all_p).id, level=random.choice(['high','critical','medium']), message=random.choice(['TCN Vision Fall Detected','Sudden Impact (Accel > 3.2g)','Extended Inactivity in Room','Missed Morning Check-in','Abnormal Night Movement']), ack=random.choice([False,False,True]), created_at=now - timedelta(days=random.randint(0,6), hours=random.randint(0,12)))) for _ in range(18)]; db.commit(); print('Rich demo data ready! Total monitored:', len(all_p)); db.close()"

echo [4/4] Opening Dashboard & AI Showcase...
start http://localhost:5173
start "" "fall_detection\reports\showcase.html"

echo.
echo ========================================================
echo  Dashboard is LIVE with 35+ Monitored People & Rich Alerts!
echo  URL  : http://localhost:5173
echo  Login: admin / admin12345678
echo ========================================================
pause