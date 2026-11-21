"""Settings read from environment variables (production refuses demo secrets)."""
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./elderlife4.db")

APP_ENV = os.getenv("APP_ENV", "development").lower()      # "production" turns every demo default off

PROD = APP_ENV == "production"

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me")

DEVICE_KEY = os.getenv("DEVICE_KEY", "dev-key")          # used by AI services / cameras posting events

if PROD:   # fail fast instead of silently running with demo credentials
    _weak = {"", "dev-secret-change-me", "dev-key", "change-me"}
    if SECRET in _weak or len(SECRET) < 32: raise RuntimeError("APP_ENV=production needs SECRET_KEY (32+ characters)")
    if DEVICE_KEY in _weak or len(DEVICE_KEY) < 16: raise RuntimeError("APP_ENV=production needs DEVICE_KEY (16+ characters)")
    if not os.getenv("ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD") in {"admin123", "change-me"} or len(os.getenv("ADMIN_PASSWORD")) < 10:
        raise RuntimeError("APP_ENV=production needs ADMIN_PASSWORD (10+ characters, not a demo value)")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*" if not PROD else "").split(",") if o.strip()]

STEP = max(1, int(os.getenv("ESCALATION_STEP_SECONDS", "30")))   # seconds between escalation stages (demo value)

VERIFY_S = int(os.getenv("VERIFY_SECONDS", "60"))        # time the person has to answer "Are you okay?" after a fall

FALL_MIN_CONF = float(os.getenv("FALL_MIN_CONFIDENCE", "0.6"))   # falls below this confidence are ignored

SNOOZE_MIN = int(os.getenv("ACK_SNOOZE_MINUTES", "30"))  # no new alert for a person after an acknowledgement

TG = os.getenv("TELEGRAM_BOT_TOKEN")

SMTP_HOST, SMTP_PORT = os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587"))

SMTP_USER, SMTP_PASS = os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")

SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "elderlife@localhost")

AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "true").lower() != "false"   # set false in production and run `alembic upgrade head`
EXPORT_KEY = os.getenv("EXPORT_KEY", "")   # optional read-only key for Power BI refresh (header X-Export-Key); empty = disabled
if PROD and EXPORT_KEY and len(EXPORT_KEY) < 16: raise RuntimeError("EXPORT_KEY must be at least 16 characters")
