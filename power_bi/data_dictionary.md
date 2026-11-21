# Data dictionary

Columns come from `GET /export/<name>` (see `backend/app/api/analytics.py`); columns marked *(Power Query)* are added by `power_query.m`.

## alerts
| Column | Meaning |
|---|---|
| id | row id |
| elderly_id | person id (joins to people) |
| level | risk level Normal/Low/Medium/High/Critical |
| reasons | why, in English |
| status | open / acknowledged / resolved |
| stage | escalation stage 1-4 |
| resolved_by | person or caregiver; empty while open |
| created_at | when created (server local time) |
| resolved_at | when closed; empty while open |
| created_date | date of created_at (Power Query) |
| level_order | 0-4 for sorting (Power Query) |

## risk
| Column | Meaning |
|---|---|
| elderly_id | person id (joins to people) |
| level | risk level Normal/Low/Medium/High/Critical |
| score | risk score 0-1 |
| created_at | when created (server local time) |
| created_date | date (Power Query) |
| level_order | 0-4 (Power Query) |

## events
| Column | Meaning |
|---|---|
| id | row id |
| elderly_id | person id (joins to people) |
| kind | event kind (activity/fall/ok/sos) or care item kind (medication/meal/water/activity) |
| value | activity level (0-100) or fall confidence (0-1) or 0 |
| created_at | when created (server local time) |
| created_date | date (Power Query) |
| hour | 0-23 (Power Query) |

## checkins
| Column | Meaning |
|---|---|
| id | row id |
| elderly_id | person id (joins to people) |
| scheduled_at | when the check-in was due |
| responded_at | when answered; empty = not answered |
| scheduled_date | date (Power Query) |

## careplan
| Column | Meaning |
|---|---|
| id | row id |
| elderly_id | person id (joins to people) |
| kind | event kind (activity/fall/ok/sos) or care item kind (medication/meal/water/activity) |
| title | care item text |
| time | HH:MM reminder time |
| done_date | yyyy-mm-dd of last completion, empty = not done |

## people
| Column | Meaning |
|---|---|
| elderly_id | person id (joins to people) |
| age | years |
| baseline_activity | person's learned usual activity level |
| checkin_time | usual HH:MM |
| caregiver_id | assigned caregiver user id |
| age_band | <70 / 70-79 / 80-89 / 90+ (Power Query) |
