# Known limitations
1. **No model is trained on real data.** SisFall, CASAS and the image dataset are not in the repository; their pipelines are written and tested on generated files only. Every reported metric is synthetic (docs/MODEL_EVALUATION.md). The backend refuses synthetic accelerometer models by default.
2. **The split backend was never run on real FastAPI/SQLAlchemy** (not installable offline). Verified by name checks, route table, pure-logic tests; the HTTP integration tests are written but were skipped. The foreign keys added to the models and `PRAGMA foreign_keys=ON` for SQLite are untested at runtime.
3. **Alembic, PostgreSQL, Docker images and compose were not executed.**
4. **Computer vision with a real camera was not run**: MediaPipe model download and camera needed. The pose classifier was trained on synthetic keypoints; real footage will behave differently.
5. **Frontend**: built with esbuild and render-tested with React 19, not with Vite/React 18 in a browser; forms, clicks and live polling were not exercised against a backend.
6. Risk and pose "retraining" use scenario/keypoint generators written by us; the numbers show the code works, not real benefit. The older numbers (risk AUC 0.941, pose 0.98, anomaly F1 0.99) were not reproducible and were removed.
7. On synthetic data the personal baseline did **not** beat a population threshold; the claim is untested on real CASAS data.
8. Security: hand-made 24 h token without revocation, in-memory login throttle (per process), no HTTPS/reverse proxy in compose, no audit log of reads. Review before any real deployment.
9. Timestamps are server local time. One person per camera. Care plan shows recorded reminders only (never diagnoses or changes doses).
10. No `.pbix`; M/DAX not opened in Power BI Desktop. Care-plan completion history is not stored (only the last done date).
11. Dataset sources/licenses: SisFall source verified, data-file license to confirm; CASAS release used by the team unconfirmed; image dataset source unknown (ml/data/DATASETS_REGISTRY.md).
