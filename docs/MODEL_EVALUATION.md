# Model evaluation

## Read this first
| Model / task | Data used for the numbers below | Status |
|---|---|---|
| Fall detection (wearable accelerometer) | **synthetic** windows | pipeline verified; **real SisFall training not run yet** (dataset not downloaded) |
| Activity recognition (accelerometer) | **synthetic** | same; synthetic task is too easy (see diagnosis) |
| Abnormal-day detection (personal vs population baseline) | **synthetic** daily totals; CASAS pipeline written, **not run on real CASAS** | pipeline verified |
| Risk model (hybrid) | **synthetic scenarios** | retrained, reproducible, installed in the backend |
| Pose activity/fall model (keypoints) | **synthetic keypoints** | retrained, reproducible, installed in the backend |
| Static fall posture from images | none | pipeline written; needs the image dataset and a MediaPipe model |

**None of these numbers is real-world performance.** They show that code paths work and how the methods behave on data we generated ourselves. Real-data numbers will appear only in `ml/reports/real_*.json` after you run the real pipelines (docs/MODEL_TRAINING.md). Earlier numbers that were shown in the app (risk AUC 0.941, pose accuracy 0.98, personal-baseline F1 0.99) came from training scripts that are not in the repository; they could not be reproduced and have been replaced (old model files kept in `ml/models/*_legacy_unreproducible.json`).

Reproduce everything: `python -m ml.training.train_accel`, `train_anomaly`, `train_risk`, `train_pose`, `python -m ml.evaluation.diagnose_activity`, then `python ml/export_metrics.py` (seed 42).

## 1. Fall detection (accelerometer, synthetic)
Subject-wise split 18/6/6 (train/val/test subjects), scaler inside the pipeline, GridSearchCV with GroupKFold(4), `class_weight=balanced`. The first version of the generator was trivially separable (every model F1 = 1.0), so it was made harder (slips without free-fall, soft impacts, random final posture, active people who sit down hard or jump).

| Model | Validation F1 | Best params |
|---|---|---|
| logreg | 0.9558 | `{'clf__C': 10}` |
| svm_rbf | 0.973 | `{'clf__C': 10, 'clf__gamma': 0.05}` |
| random_forest | 0.9565 | `{'clf__max_depth': None, 'clf__n_estimators': 300}` |
| gradient_boosting | 0.9381 | `{'clf__learning_rate': 0.05, 'clf__max_depth': 3, 'clf__n_estimators': 200}` |

Selected **svm_rbf** (validation F1; differences are within noise for 6 validation subjects). Test: precision 0.9821, recall 0.9483, F1 0.9649, ROC-AUC 0.9996, AP 0.9988. Plots: `ml/reports/synthetic_fall_roc_pr.png`, `synthetic_fall_confusion.png`.

## 2. Activity recognition (synthetic) and why macro-F1 was 1.0
| Model | Validation macro-F1 |
|---|---|
| logreg | 1.0 |
| svm_rbf | 1.0 |
| random_forest | 1.0 |
| gradient_boosting | 0.9684 |

Diagnosis (`ml/reports/synthetic_activity_diagnosis.json`): No leakage found: folds are subject-wise and there are no duplicate rows. No single feature separates the classes (best single-feature macro-F1 0.77), but the combination of features does, because the generator gives every ADL a fixed posture/frequency signature plus small noise. So 1.0 means the synthetic task is easy, not that the split is broken. Real activity data will be harder; do not quote this number. Best single feature alone: z_mean = 0.77. Duplicate feature rows: 0. **Do not quote the 1.0.**

## 3. Abnormal-day detection (synthetic daily totals, 10 held-out people)
| Method | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| personal baseline | 0.6 | 0.913 | 0.7241 | 0.9922 |
| population threshold | 0.9333 | 0.6087 | 0.7368 | 0.9913 |
| isolation forest | 0.46 | 1.0 | 0.6301 | 0.9742 |

On this synthetic set the personal baseline is **not better** than a population threshold (F1 difference within noise for 10 people). The claim that personal baselines help is unproven here. `ml/training/casas_baselines.py` tests it on real CASAS home-days with leave-one-home-out and injected anomalies; not run yet.

## 4. Risk model (synthetic scenarios)
Scenario generator in `ml/training/train_risk.py` (8 situations, 3% label noise, policy: a fall is "needs a human" only after the 60 s verification window). Train 8000 / validation 4000 / test 8000, different seeds. Thresholds: `high` maximises validation F1; `low` = score reached by only 5% of fine validation days; `medium` in between.

| Method (High+ alerts) | Precision | Recall | False alerts /1000 | AP | ROC-AUC |
|---|---|---|---|---|---|
| hand-written rules | 0.7103 | 0.8072 | 45.9 | 0.7021 | 0.8915 |
| logistic model only | 0.7052 | 0.826 | 48.1 | 0.7785 | 0.8942 |
| hybrid (model + safety floor) | 0.7052 | 0.826 | 48.1 | 0.7785 | 0.8942 |

Prevalence in test: 0.1394. The model has somewhat higher recall and AP than the rules at similar precision in these scenarios. The generator and the rules are both ours, so this is not evidence of real benefit. The safety floor (SOS gives Critical, unanswered verified fall gives High) is never learned away.

## 5. Pose model (synthetic keypoints, 8 held-out people, 720 samples)
| | Accuracy | Fall precision | Fall recall | Fall false positives |
|---|---|---|---|---|
| model | 0.9889 | 1.0 | 1.0 | 0 |
| rules | 0.9056 | 0.9231 | 1.0 | 10 |

Real camera footage (lighting, occlusion, MediaPipe jitter) will behave differently. Not validated on a camera yet.

## 6. Real data: what is ready to run
`python -m ml.preprocessing.sisfall <SisFall dir>` then `python -m ml.evaluation.eda_sisfall` then `python -m ml.training.train_sisfall` (subject-wise split, thresholds tuned on validation, false-alarm rate on elderly ADLs). Same for CASAS (`ml.preprocessing.casas`, `ml.evaluation.eda_casas`, `ml.training.casas_baselines`) and images (`ml.preprocessing.fall_images`, `ml.training.train_fall_images`). Each was tested only on files generated in the real formats.
