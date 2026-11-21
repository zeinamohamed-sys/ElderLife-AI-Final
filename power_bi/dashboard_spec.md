# Report layout (4 pages, 16:9). Fields refer to tables in power_query.m and measures in measures.dax.
Global slicers (synced): `Date[Date]` range, `people[age_band]`, `people[caregiver_id]`. Theme: level colours Normal #2e8b57, Low #8fbf3f, Medium #e0a800, High #e67e22, Critical #c0392b.

## 1. Overview
- Cards: **People**, **Open Alerts**, **High+ Alerts**, **Falls Last 7 Days**, **Check-in Answer %**, **Resolved By Person %**.
- Line + columns: alerts per day (`Date[Date]`, [Alerts]) with [High+ Alerts] as second series.
- Stacked column: alerts by `alerts[level]` per week, sorted by `level_order`.
- Table: top 10 open alerts (`alerts[created_at]`, `people[elderly_id]`, `alerts[level]`, `alerts[reasons]`), filter status = open.

## 2. Risk
- Line: [Avg Risk Score] by day; small multiples by `people[age_band]`.
- Heat map (matrix): rows `people[elderly_id]`, columns `Date[Date]` (week), values [Max Risk Level], conditional colour by value 0-4.
- Bar: [People At High Risk] by caregiver.
- Decomposition tree: [High+ Alerts] by `alerts[reasons]` (what drives alerts).

## 3. Falls and activity
- Column: [Falls] by `events[hour]` (when do falls happen).
- Line: [Avg Activity] by day with [Activity vs Baseline %] as tooltip; reference line at 60% (the app flags below 60% of baseline).
- Scatter: x = [Avg Activity], y = [Falls], detail `people[elderly_id]`.
- Card: [SOS Presses].

## 4. Check-ins and care plan
- Gauge: [Check-in Answer %] (target 95%).
- Column: answered vs missed check-ins by weekday.
- Card: [Avg Check-in Delay Min].
- Matrix: `careplan[kind]` x [Care Items], [Care Items Done Today], [Care Done Today %]. Note: the export only holds the last completion date, not a history.

## Caveats to show on the report
"Resolved by person" is a proxy for false alarms, not a verified rate. Care-plan completion has no history. Timestamps are server local time.
