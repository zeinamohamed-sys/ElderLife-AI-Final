# Power BI

Everything lives in **`power_bi/`**: `README.md` (steps), `power_query.m`, `measures.dax`, `data_dictionary.md`, `dashboard_spec.md`, `sample_data/` (synthetic), `tests/test_assets.py` (checks every column used against the backend's real export code).

No `.pbix` was created (Power BI Desktop is required). Scheduled refresh uses the read-only `EXPORT_KEY` (header `X-Export-Key`, `GET /export/<alerts|risk|events|checkins|careplan|people>`), implemented in `backend/app/security.py` (`export_auth`).
