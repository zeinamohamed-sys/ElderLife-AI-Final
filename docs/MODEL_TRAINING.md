# Model training (reproduce)

All commands run from the repository root. Python 3.12, `pip install -r ml/requirements.txt` (and `xgboost` if you want it in the comparison). Seeds are fixed (42).

## A. Synthetic pipeline checks (works offline; results are NOT real performance)
```
python -m ml.training.train_accel        # fall + activity on generated accelerometer windows
python -m ml.training.train_anomaly      # personal vs population baseline vs Isolation Forest on generated daily totals
python -m ml.training.train_risk [--install]   # risk model vs rules, scenario generator
python -m ml.training.train_pose [--install]   # pose model vs rules, keypoint generator
python -m ml.evaluation.diagnose_activity
python ml/export_metrics.py              # rewrites backend/app/models/metrics.json from the reports
```
`--install` copies the model into `backend/app/models/` (already done in this delivery for the risk and pose models; the previous files are kept as `ml/models/*_legacy_unreproducible.json`).

## B. SisFall (real accelerometer data)
```
python -m ml.data.download_datasets status
python -m ml.preprocessing.sisfall ml/data/raw/sisfall            # ~4510 files -> ml/data/processed/sisfall_features.csv.gz
python -m ml.evaluation.eda_sisfall                                # class balance, peaks per activity, adults vs elderly
python -m ml.training.train_sisfall [--max-train 30000]            # tuned RF / HistGB / SVM / LogReg (+ XGBoost if installed)
python ml/export_to_backend.py                                     # copies ml/models/real_sisfall_fall.joblib into the backend
```
Protocol: split by subject (adults 60/20/20; SE06 in train; other elderly 60/20/20), scaler inside the pipeline, GridSearchCV + GroupKFold on training subjects (capped, fall-preserving subsample), model chosen by validation average precision, alert threshold chosen on validation (highest precision at recall >= 0.95) and frozen, test touched once. Extra checks: false-alarm rate on elderly ADL windows and per ADL code (D11 collapse, D18 stumble, D19 jump are the usual troublemakers). Outputs: `ml/reports/real_sisfall_fall_metrics.json`, `real_sisfall_activity_metrics.json`, ROC/PR and confusion PNGs, `ml/models/real_sisfall_*.joblib` (metadata `data = "real:SisFall"`, which is what lets the backend accept the model).
Training on a laptop: expect minutes to tens of minutes (SVM probability is the slowest; use `--max-train`).

## C. CASAS
```
python -m ml.preprocessing.casas ml/data/raw/casas
python -m ml.evaluation.eda_casas
python -m ml.training.casas_baselines --calib-days 30 --rate 0.1
```
Leave-one-home-out, same threshold protocol for personal, population and Isolation Forest, injected anomalies (inactivity, night wandering, routine shift) on held-out days, bootstrap interval for the F1 difference. Needs at least 3 homes with 45+ usable days.

## D. Fall images
```
python computer_vision/download_pose_model.py
python -m ml.preprocessing.fall_images <images root> --classes "0:fall,1:standing"
python -m ml.training.train_fall_images
```
Group-wise split by source video. Needs `pip install mediapipe opencv-python`.

## Test status of these scripts
Every script above was executed in the sandbox only on **generated data in the same file formats** (`ml/tests/`), never on the real datasets. Real runs may reveal format differences (column names, delimiters, folder layout): fix the constants at the top of the preprocessing scripts and report.
