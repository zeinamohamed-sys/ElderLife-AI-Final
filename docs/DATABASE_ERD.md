# Database design

Source of truth: `database/migrations/0001_initial.sql` (copied to `data_preparation_and_db/schema.sql`). It matches the SQLAlchemy models in `backend/app/main.py` and adds the foreign keys and CHECK constraints the models do not declare yet (the running app stores the ids as plain integers). Verified by loading it into SQLite with foreign keys on and checking that a bad FK and a bad `events.kind` are rejected. Not yet verified on PostgreSQL.

```mermaid
erDiagram
    users ||--o{ elderly : "looks after (caregiver_id)"
    users ||--o{ notifications : receives
    elderly ||--o{ checkins : has
    elderly ||--o{ events : has
    elderly ||--o{ alerts : has
    elderly ||--o{ careplan : has
    elderly ||--o{ risklog : has
    alerts ||--o{ notifications : "sent for"
    users { int id PK  string username UK  string role  string email  string telegram_chat_id  string lang }
    elderly { int id PK  string name  int age  float baseline_activity  string checkin_time  int caregiver_id FK  string emergency_contact  string access_code UK }
    checkins { int id PK  int elderly_id FK  datetime scheduled_at  datetime responded_at }
    events { int id PK  int elderly_id FK  string kind  float value  datetime created_at }
    alerts { int id PK  int elderly_id FK  string level  string reasons  string status  int stage  string resolved_by }
    careplan { int id PK  int elderly_id FK  string kind  string title  string time  string done_date }
    risklog { int id PK  int elderly_id FK  string level  float score  datetime created_at }
    notifications { int id PK  int user_id FK  int alert_id FK  string text }
```

## Planned tables (`0002_planned_ml_tables.sql`, not used by the app yet)
`activity_baselines` (per person and hour) and `ml_predictions` (audit of model outputs). Today the baseline is one number in `elderly.baseline_activity`.

## Notes
- Roles are `admin` and `caregiver` (the person uses an access code, not a user row).
- `alerts.reasons` stores message keys plus parameters, translated when read.
- Timestamps are server local time (a known limitation, see LIMITATIONS.md).
- The old 5-table schema (`sensor_logs`, `fall_alerts`, ...) did not match the app and was replaced.
