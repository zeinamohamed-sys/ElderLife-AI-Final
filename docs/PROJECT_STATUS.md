# Project status (end of phase 2)

Legend: **Done** = code exists. **Tested** = executed here (see TESTING_REPORT.md). **Pending** = not done or needs your environment.

## Backend and database
| Item | Done | Tested | Pending |
|---|---|---|---|
| main.py split into core/db/security/services/api modules, logging, same 31 original routes | yes | route table + name check + logic tests | run against real FastAPI |
| Foreign keys in models, SQL migrations, Alembic baseline, `init_db.py` | yes | SQL in SQLite (FK/CHECK probes) | Alembic, PostgreSQL |
| Input validation (pydantic limits), login throttle (429), production refuses demo secrets, device-key constant-time compare | yes | throttle + export key unit tests; validation not run | HTTP tests |
| New endpoints: `/dashboard/summary`, `/events`, `/checkins`, `/careplan`, `/elderly/{id}/timeline`, `/sensor/accel`, `/sensor/accel/model`, read-only `EXPORT_KEY` | yes | summary maths, accel wrapper, route table | queries untested against a DB |
| Risk model and pose model retrained reproducibly and installed; metrics.json rebuilt from reports | yes | backend tests pass with them | real-data validation |

## Frontend (React, English/Arabic, RTL)
| Item | Done | Tested | Pending |
|---|---|---|---|
| Pages: Login, Overview dashboard, People (profiles + detail), Alerts, Check-ins, Events, Care plans, Analytics, Notifications, Admin (caregiver management), Settings | yes | render of every state, both languages (34 tests) | browser run against the backend |
| Charts: risk levels, alerts/falls per day, activity trend, risk trend, caregiver table; loading/empty/error states with retry | yes | rendered | visual review |

## Computer vision
Pipeline, webcam/video monitor, MediaPipe wrapper, privacy (no frames kept), thresholds: **done; pipeline logic and video reading tested; MediaPipe and webcam pending** (needs the model download and a camera).

## Machine learning
| Item | Done | Real-data result |
|---|---|---|
| SisFall loader/windowing/EDA/training (subject-wise, threshold on validation, elderly false-alarm check), export to backend, `/sensor/accel` | yes | **none: dataset not downloaded** |
| CASAS loader, behavioural patterns, EDA, personal vs population vs Isolation Forest (leave-one-home-out, injected anomalies) | yes | **none** |
| Fall-image pipeline (validate, dedupe, group, MediaPipe keypoints, group-wise training) | yes | **none** |
| Activity macro-F1 = 1.0 investigated | yes | synthetic task is easy, no leakage found |
| Risk and pose models, synthetic benchmarks | yes | synthetic only |

## Power BI
Power Query, 25 DAX measures, data dictionary, 4-page spec, synthetic sample CSVs, consistency tests: **done and tested against the backend's export code; not opened in Power BI Desktop; no `.pbix`**.

## Deployment
`docker-compose.yml`, Dockerfiles, `.env.example`, health checks, migrations on start: **written, YAML-checked, not run**.

## Your next steps (in order)
1. `pip install -r backend/requirements-dev.txt && python tests/run_all.py`: fix what the 7 API tests reveal.
2. `cp .env.example .env`, fill secrets, `docker compose up --build`.
3. Download SisFall (docs/MODEL_TRAINING.md section B), run the pipeline, read `ml/reports/real_sisfall_*`, then `python ml/export_to_backend.py`.
4. Put CASAS files in `ml/data/raw/casas/`, run section C; record the real source/license of every dataset in `ml/data/DATASETS_REGISTRY.md`.
5. Images: `python computer_vision/download_pose_model.py`, test `monitor.py` with a webcam, then section D.
6. Build the Power BI report from `power_bi/`.
