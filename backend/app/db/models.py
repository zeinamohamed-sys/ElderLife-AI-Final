"""SQLAlchemy models (foreign keys match database/migrations/0001_initial.sql)."""
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from app.core.config import AUTO_CREATE_TABLES
from app.db.database import Base, engine, ensure_columns, now

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    salt = Column(String); pw = Column(String)
    role = Column(String, default="caregiver")  # admin | caregiver
    telegram_chat_id = Column(String, nullable=True)
    email = Column(String, nullable=True)
    lang = Column(String, default="en")         # language of the email/Telegram alerts this user receives

class Elderly(Base):
    __tablename__ = "elderly"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False); age = Column(Integer)
    baseline_activity = Column(Float, default=50)
    checkin_time = Column(String, default="09:00")
    caregiver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    emergency_contact = Column(String, default="")
    access_code = Column(String, unique=True)           # opens the person's own screen
    silenced_at = Column(DateTime, nullable=True); silenced_until = Column(DateTime, nullable=True)

class CheckIn(Base):
    __tablename__ = "checkins"
    id = Column(Integer, primary_key=True); elderly_id = Column(Integer, ForeignKey("elderly.id", ondelete="CASCADE"), index=True, nullable=False)
    scheduled_at = Column(DateTime); responded_at = Column(DateTime, nullable=True)

class Event(Base):  # kind: activity | fall (value = confidence) | ok | sos
    __tablename__ = "events"
    id = Column(Integer, primary_key=True); elderly_id = Column(Integer, ForeignKey("elderly.id", ondelete="CASCADE"), index=True, nullable=False)
    kind = Column(String); value = Column(Float, default=0); created_at = Column(DateTime, default=now)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True); elderly_id = Column(Integer, ForeignKey("elderly.id", ondelete="CASCADE"), index=True, nullable=False)
    level = Column(String); reasons = Column(String)
    status = Column(String, default="open")  # open | acknowledged | resolved
    stage = Column(Integer, default=1)
    resolved_by = Column(String, nullable=True)  # person | caregiver
    created_at = Column(DateTime, default=now); resolved_at = Column(DateTime, nullable=True)

class CarePlanItem(Base):  # reminders only: recorded plan, no diagnosis or dose changes
    __tablename__ = "careplan"
    id = Column(Integer, primary_key=True); elderly_id = Column(Integer, ForeignKey("elderly.id", ondelete="CASCADE"), index=True, nullable=False)
    kind = Column(String); title = Column(String); time = Column(String)
    note = Column(String, default=""); done_date = Column(String, nullable=True)

class RiskLog(Base):
    __tablename__ = "risklog"
    id = Column(Integer, primary_key=True); elderly_id = Column(Integer, ForeignKey("elderly.id", ondelete="CASCADE"), index=True, nullable=False)
    level = Column(String); score = Column(Float); created_at = Column(DateTime, default=now)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True); user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE")); text = Column(String); created_at = Column(DateTime, default=now)

if AUTO_CREATE_TABLES: Base.metadata.create_all(engine)

ensure_columns("users", {"lang": "VARCHAR(8) DEFAULT 'en'"})
