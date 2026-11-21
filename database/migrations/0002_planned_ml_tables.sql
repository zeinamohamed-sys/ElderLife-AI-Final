-- PLANNED, NOT USED BY THE APP YET. Apply only together with the backend change that writes to them.
CREATE TABLE IF NOT EXISTS activity_baselines (   -- per-person, per-hour baseline (today only one number lives in elderly.baseline_activity)
    id INTEGER PRIMARY KEY,
    elderly_id INTEGER NOT NULL REFERENCES elderly(id) ON DELETE CASCADE,
    hour_of_day INTEGER NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    mean_activity FLOAT NOT NULL, std_activity FLOAT, n_days INTEGER NOT NULL, updated_at TIMESTAMP,
    UNIQUE (elderly_id, hour_of_day)
);
CREATE TABLE IF NOT EXISTS ml_predictions (       -- audit trail of every model output
    id INTEGER PRIMARY KEY,
    elderly_id INTEGER NOT NULL REFERENCES elderly(id) ON DELETE CASCADE,
    model_name VARCHAR NOT NULL, model_version VARCHAR, kind VARCHAR NOT NULL,
    label VARCHAR, probability FLOAT, features_json VARCHAR, created_at TIMESTAMP
);
