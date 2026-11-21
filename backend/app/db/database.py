"""Engine, session factory and declarative Base."""
from datetime import datetime
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import DB_URL

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

now = datetime.now  # all timestamps use server local time

def ensure_columns(table, columns):   # tiny migration for databases created by an older version
    have = {c["name"] for c in inspect(engine).get_columns(table)}
    with engine.begin() as conn:
        for name, ddl in columns.items():
            if name not in have: conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

if DB_URL.startswith("sqlite"):   # SQLite ignores foreign keys unless asked; PostgreSQL always enforces them
    @event.listens_for(engine, "connect")
    def _sqlite_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
