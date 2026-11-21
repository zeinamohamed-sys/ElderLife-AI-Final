# Deployment (not executed in the authoring sandbox: Docker was unavailable)
1. `cp .env.example .env` and fill `SECRET_KEY`, `DEVICE_KEY`, `ADMIN_PASSWORD`, `POSTGRES_PASSWORD`, `CORS_ORIGINS`, `VITE_API`.
2. `docker compose up --build` -> frontend http://localhost:5173, API http://localhost:8000/docs, data in the `pgdata` volume.
3. With `APP_ENV=production` the backend **refuses to start** with demo secrets or a weak admin password, disables `/simulate/seed`, uses `CORS_ORIGINS` (no `*`), and compares the device key in constant time. The first start creates the admin from `ADMIN_USERNAME`/`ADMIN_PASSWORD`.
4. Development without Docker: see README. Demo logins (`admin/admin123`, `sara/care123`) exist only when `APP_ENV` is not `production`.
5. Still to do: HTTPS reverse proxy, backups of `pgdata`, rate limiting on `/auth/login`.

## Added in phase 2
- Migrations: the backend image sets `AUTO_CREATE_TABLES=false` and runs `alembic upgrade head` before starting (baseline `0001` adopts databases created earlier). For local development without Alembic leave `AUTO_CREATE_TABLES` unset (tables are created at start).
- `EXPORT_KEY` (16+ chars, optional): read-only key for Power BI refresh, header `X-Export-Key`, only on `/export/*`.
- Wearable accelerometer model: build the image with `--build-arg WITH_ML=true`, train on real SisFall, `python ml/export_to_backend.py`, mount/copy `accel_fall.joblib` into `backend/app/models/`. Without it `/sensor/accel` answers 503 (by design).
- Login throttle: 5 wrong passwords per username in 5 minutes gives HTTP 429 (per process).
- Camera machine: `computer_vision/monitor.py` runs next to the camera, not in Docker; it only needs network access to the API and `DEVICE_KEY`.
