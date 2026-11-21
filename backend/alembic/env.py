"""Alembic environment. Usage (from backend/):  alembic upgrade head   |   alembic revision --autogenerate -m "message"
NOT executed in the authoring sandbox (alembic is not installable offline): run it on your machine and report problems."""
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine
from app.core.config import DB_URL
from app.db.database import Base
import app.db.models  # noqa: F401  (registers the tables on Base.metadata)
if context.config.config_file_name: fileConfig(context.config.config_file_name)
target_metadata = Base.metadata
def run_migrations_offline():
    context.configure(url=DB_URL, target_metadata=target_metadata, literal_binds=True, render_as_batch=DB_URL.startswith("sqlite")); 
    with context.begin_transaction(): context.run_migrations()
def run_migrations_online():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=target_metadata, render_as_batch=DB_URL.startswith("sqlite"))
        with context.begin_transaction(): context.run_migrations()
(run_migrations_offline if context.is_offline_mode() else run_migrations_online)()
