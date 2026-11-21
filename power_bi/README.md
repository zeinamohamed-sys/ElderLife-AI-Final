# Power BI

**No `.pbix` file is included**: it cannot be produced outside Power BI Desktop. Everything needed to build it in about 30 minutes is here, and every file was checked against the backend's real export columns by `power_bi/tests/test_assets.py`. The M and DAX code was **not opened in Power BI Desktop** by me; expect small fixes.

## Files
| File | What |
|---|---|
| `power_query.m` | Power Query for the 6 exports (types, date columns, level order, age bands) |
| `measures.dax` | 25 measures + the Date table and relationship notes |
| `data_dictionary.md` | every column of every export |
| `dashboard_spec.md` | 4 report pages with each visual, fields and filters |
| `sample_data/*.csv` | **SYNTHETIC** exports in the exact format (made by `build_sample_exports.py`, 24 people, 60 days) so you can design the report before a backend exists; replace with live data later |
| `build_sample_exports.py` | regenerates the sample files |

## Steps
1. Start the backend with `EXPORT_KEY=<16+ random characters>` in `.env` (read-only key, works only on `/export/*`, sees all people). Or use a caregiver token instead (expires in 24 h, so no scheduled refresh).
2. Power BI Desktop > Transform data > Manage parameters: `BaseUrl` (e.g. `http://localhost:8000`) and `ExportKey`.
3. Paste `power_query.m` queries (helper first, named `fnExport`; then one query per table named exactly `alerts`, `risk`, `events`, `checkins`, `careplan`, `people`).
4. Model view: create `Date`, add the relationships listed at the top of `measures.dax`.
5. Paste measures, build the pages in `dashboard_spec.md`.
6. Publish. For scheduled refresh through the Power BI service the backend must be reachable from the gateway/cloud; store `ExportKey` in the dataset credentials/parameters.
Offline alternative: `Get Data > Text/CSV` on `sample_data/*.csv` (or CSVs downloaded from the app's Analytics page) and name the tables the same.

## Privacy
`people` has no names, contacts or access codes. Alert reasons are English text. Do not publish a report with real data to a public tenant.
