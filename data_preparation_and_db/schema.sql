-- ElderLife AI: schema that matches backend/app/main.py (SQLAlchemy models), plus the constraints the models do not enforce yet.
-- Portable SQL (SQLite and PostgreSQL). Apply with: python database/init_db.py
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username VARCHAR NOT NULL UNIQUE,
    salt VARCHAR NOT NULL,
    pw VARCHAR NOT NULL,                       -- PBKDF2-SHA256 hash
    role VARCHAR NOT NULL DEFAULT 'caregiver' CHECK (role IN ('admin','caregiver')),
    telegram_chat_id VARCHAR,
    email VARCHAR,
    lang VARCHAR(8) DEFAULT 'en'
);
CREATE TABLE IF NOT EXISTS elderly (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    age INTEGER CHECK (age IS NULL OR age BETWEEN 0 AND 120),
    baseline_activity FLOAT DEFAULT 50,        -- personal activity baseline, learned by tick()
    checkin_time VARCHAR DEFAULT '09:00',
    caregiver_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    emergency_contact VARCHAR DEFAULT '',
    access_code VARCHAR UNIQUE,                -- opens the person's own screen
    silenced_at TIMESTAMP, silenced_until TIMESTAMP
);
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY,
    elderly_id INTEGER NOT NULL REFERENCES elderly(id) ON DELETE CASCADE,
    scheduled_at TIMESTAMP NOT NULL, responded_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS events (            -- kind: activity | fall (value = confidence) | ok | sos
    id INTEGER PRIMARY KEY,
    elderly_id INTEGER NOT NULL REFERENCES elderly(id) ON DELETE CASCADE,
    kind VARCHAR NOT NULL CHECK (kind IN ('activity','fall','ok','sos')),
    value FLOAT DEFAULT 0, created_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY,
    elderly_id INTEGER NOT NULL REFERENCES elderly(id) ON DELETE CASCADE,
    level VARCHAR NOT NULL, reasons VARCHAR,   -- message keys + params (JSON), translated at read time
    status VARCHAR DEFAULT 'open' CHECK (status IN ('open','acknowledged','resolved')),
    stage INTEGER DEFAULT 1,
    resolved_by VARCHAR CHECK (resolved_by IS NULL OR resolved_by IN ('person','caregiver')),
    created_at TIMESTAMP, resolved_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS careplan (          -- recorded reminders only: no diagnosis, no dose changes
    id INTEGER PRIMARY KEY,
    elderly_id INTEGER NOT NULL REFERENCES elderly(id) ON DELETE CASCADE,
    kind VARCHAR, title VARCHAR, time VARCHAR, note VARCHAR DEFAULT '', done_date VARCHAR
);
CREATE TABLE IF NOT EXISTS risklog (
    id INTEGER PRIMARY KEY,
    elderly_id INTEGER NOT NULL REFERENCES elderly(id) ON DELETE CASCADE,
    level VARCHAR, score FLOAT, created_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    text VARCHAR, created_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_checkins_elderly ON checkins(elderly_id);
CREATE INDEX IF NOT EXISTS ix_events_elderly ON events(elderly_id);
CREATE INDEX IF NOT EXISTS ix_alerts_elderly ON alerts(elderly_id);
CREATE INDEX IF NOT EXISTS ix_careplan_elderly ON careplan(elderly_id);
CREATE INDEX IF NOT EXISTS ix_risklog_elderly ON risklog(elderly_id);
