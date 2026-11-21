# Main dashboard (Overview page)

The dashboard is the **Overview** tab of the React app (`frontend/src/pages.jsx`, `OverviewView`). Every widget reads `GET /dashboard/summary`, computed in `backend/app/services/dashboard.py` from stored rows (no hard-coded values). The page refreshes every 10 s.

| Widget | Field in `/dashboard/summary` | Notes |
|---|---|---|
| Total people | `totals.people` | scoped to the user (admin: everyone, caregiver: assigned people) |
| Safety status | `safety.status` ok / attention / critical | critical = a Critical alert or person; attention = open/acknowledged alerts or Medium/High people |
| Active and critical alerts | `alerts.open`, `alerts.high_or_critical_open`, `alerts.acknowledged` | |
| Daily check-ins | `checkins_today.{due,answered,missed,pending}` | missed = unanswered 30+ min after its time |
| Fall incidents | `falls.today`, `falls.last_7_days`, `falls.per_day` | |
| Risk levels | `safety.levels` | live evaluation of each person |
| Activity trend | `activity_trend[].mean` (14 days) | mean of `activity` events; gaps = no data |
| Behavioural anomalies | `anomalies[]` | activity below 60% of the person's baseline today, or a missed check-in |
| Recent events | `recent_events[]` | last 10 across the user's people |
| Caregiver activity | `caregivers[]` | people, open alerts, alerts closed in 7 days, average response minutes |

Other pages (Alerts, Check-ins, Events, Care plans, Analytics, Notifications, Admin = caregiver management, Settings) use `/alerts`, `/checkins`, `/events`, `/careplan`, `/analytics`, `/notifications`, `/users` + `/admin/people`.
Tests: `frontend/tests/views.test.jsx` (render of every state) and `backend/tests/test_dashboard.py` (the maths).
