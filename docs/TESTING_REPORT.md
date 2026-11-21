# Testing report (executed in the authoring sandbox, 2026-11-21, Python 3.12, Node 22)

Run everything: `python tests/run_all.py` (frontend needs `npm install` in `frontend/`, or `FRONTEND_NODE_MODULES`).

| Suite | Ran | Passed | Failed | Skipped | Notes |
|---|---|---|---|---|---|
| backend: risk/vision/i18n logic, route table, dashboard maths, login throttle, export key, accelerometer wrapper | 52 | 45 | 0 | **7** | the 7 skipped are `test_api.py` (HTTP-level auth/role/validation tests): **not run** because FastAPI/httpx cannot be installed offline |
| ml: features, SisFall loader/windowing/training, CASAS loader/baselines/EDA, image pipeline, inference | 17 | 17 | 0 | 0 | all on files **generated in the real formats**; nothing here measures accuracy on real data |
| computer_vision: pipeline (fake extractor), real video file read with OpenCV | 7 | 7 | 0 | 0 | MediaPipe itself not run |
| power_bi: sample CSV headers vs backend export code, DAX/M column references | 5 | 5 | 0 | 0 | M/DAX not opened in Power BI Desktop |
| frontend: render of every state in English and Arabic, locale parity, chart maths | 34 | 34 | 0 | 0 | run with **React 19** from the sandbox (the project pins 18.3), static rendering only |
| static name check (`tools/check_names.py`, all Python) | 1 | 1 | 0 | 0 | undefined names / unused imports |
| SQL migration `0001` in SQLite with FK and CHECK probes | manual | passed | | | not a test file; PostgreSQL not tried |
| `docker-compose.yml` parses as YAML | manual | passed | | | Docker itself not available: images **not built, containers not started** |

## Bugs found by the tests and fixed
- CASAS loader dropped every timestamp that had a different fractional-seconds format from the first line (real CASAS logs mix both): now `format="mixed"`.
- First synthetic fall benchmark was trivially separable (all models F1 = 1.0): generator made harder.
- Retrained risk model first produced "Low" for a normal day and Critical during the 60 s fall verification: label policy and thresholds fixed; backend tests pass with it.
- A scripted edit broke a test file; caught by running it.

## Not tested at all
Real FastAPI + SQLAlchemy behaviour of the split backend (only static checks, route table and pure-logic tests), Alembic, PostgreSQL, Docker, browser behaviour (clicks, forms, network), webcam, MediaPipe, any real dataset.

## Reproduce
`python tests/run_all.py`; individual: `cd backend && python -m unittest discover -s tests`; `python -m unittest discover -s ml/tests -t .`; `python -m unittest discover -s computer_vision/tests -t .`; `python -m unittest power_bi.tests.test_assets`; `cd frontend && npm test`. With FastAPI installed (`pip install -r backend/requirements-dev.txt`) the 7 API tests run too; expect to fix whatever they reveal.
