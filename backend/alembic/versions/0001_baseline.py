"""Baseline: the schema of database/migrations/0001_initial.sql, created only for tables that do not exist yet
(so databases that the app created with create_all can be adopted with `alembic upgrade head`).
Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa
revision = "0001"; down_revision = None; branch_labels = None; depends_on = None
def _missing(name): return not sa.inspect(op.get_bind()).has_table(name)
def upgrade():
    fk = lambda col: sa.ForeignKey(col, ondelete="CASCADE")
    if _missing("users"):
        op.create_table("users", sa.Column("id", sa.Integer, primary_key=True), sa.Column("username", sa.String, unique=True),
            sa.Column("salt", sa.String), sa.Column("pw", sa.String), sa.Column("role", sa.String), sa.Column("telegram_chat_id", sa.String),
            sa.Column("email", sa.String), sa.Column("lang", sa.String(8)))
    if _missing("elderly"):
        op.create_table("elderly", sa.Column("id", sa.Integer, primary_key=True), sa.Column("name", sa.String, nullable=False), sa.Column("age", sa.Integer),
            sa.Column("baseline_activity", sa.Float), sa.Column("checkin_time", sa.String), sa.Column("caregiver_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
            sa.Column("emergency_contact", sa.String), sa.Column("access_code", sa.String, unique=True),
            sa.Column("silenced_at", sa.DateTime), sa.Column("silenced_until", sa.DateTime))
    if _missing("checkins"):
        op.create_table("checkins", sa.Column("id", sa.Integer, primary_key=True), sa.Column("elderly_id", sa.Integer, fk("elderly.id"), nullable=False, index=True),
            sa.Column("scheduled_at", sa.DateTime), sa.Column("responded_at", sa.DateTime))
    if _missing("events"):
        op.create_table("events", sa.Column("id", sa.Integer, primary_key=True), sa.Column("elderly_id", sa.Integer, fk("elderly.id"), nullable=False, index=True),
            sa.Column("kind", sa.String), sa.Column("value", sa.Float), sa.Column("created_at", sa.DateTime))
    if _missing("alerts"):
        op.create_table("alerts", sa.Column("id", sa.Integer, primary_key=True), sa.Column("elderly_id", sa.Integer, fk("elderly.id"), nullable=False, index=True),
            sa.Column("level", sa.String), sa.Column("reasons", sa.String), sa.Column("status", sa.String), sa.Column("stage", sa.Integer),
            sa.Column("resolved_by", sa.String), sa.Column("created_at", sa.DateTime), sa.Column("resolved_at", sa.DateTime))
    if _missing("careplan"):
        op.create_table("careplan", sa.Column("id", sa.Integer, primary_key=True), sa.Column("elderly_id", sa.Integer, fk("elderly.id"), nullable=False, index=True),
            sa.Column("kind", sa.String), sa.Column("title", sa.String), sa.Column("time", sa.String), sa.Column("note", sa.String), sa.Column("done_date", sa.String))
    if _missing("risklog"):
        op.create_table("risklog", sa.Column("id", sa.Integer, primary_key=True), sa.Column("elderly_id", sa.Integer, fk("elderly.id"), nullable=False, index=True),
            sa.Column("level", sa.String), sa.Column("score", sa.Float), sa.Column("created_at", sa.DateTime))
    if _missing("notifications"):
        op.create_table("notifications", sa.Column("id", sa.Integer, primary_key=True), sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
            sa.Column("alert_id", sa.Integer, fk("alerts.id")), sa.Column("text", sa.String), sa.Column("created_at", sa.DateTime))
def downgrade():
    for t in ("notifications", "risklog", "careplan", "alerts", "events", "checkins", "elderly", "users"): op.drop_table(t)
