# EDA report

## Status: no real-data EDA has been run yet
The three real datasets are not in the repository and the authoring environment had no internet, so there are **no real EDA findings to report**. What exists:

| Dataset | EDA code | What it produces | Executed on |
|---|---|---|---|
| SisFall | `ml/evaluation/eda_sisfall.py` | counts per activity class and group (adult/elderly), fall fraction, missing values, peak-acceleration box plots per activity code, ADL vs fall peak histograms | generated SisFall-format files only (to prove it runs) |
| CASAS | `ml/evaluation/eda_casas.py` | typical hourly profile per home, daily motion distribution, weekday/weekend means, night share, routine-regularity score | generated CASAS-format logs only |
| Fall images | `ml/preprocessing/fall_images.py` | rejected counts (unreadable, too small, duplicate, no label), groups, label counts | generated images only |
| Notebook | `data_preparation_and_db/elder_ai.ipynb` | the team's own health checks: 374 train + 111 val images with no corrupt files; 2,059,199 rows in `atmo1.csv`; 162,500 rows in accelerometer file 1.csv with a few hundred dropped by cleaning | team's data (their notebook, not re-run by me) |

Synthetic generator EDA: `ml/evaluation/diagnose_activity.py` examines the synthetic activity data (see MODEL_EVALUATION.md section 2).

## When you run the real pipelines
Run the EDA scripts first and paste the printed summary and `ml/reports/real_*_eda_*.png` here. Things to check explicitly: class imbalance (SisFall falls are a small share of windows), per-subject differences, whether elderly peaks differ from adults, CASAS logging gaps and per-home sensor counts, duplicate frames in the image set.
