# Feature engineering

## Accelerometer window (3 s, 50 Hz, in g) - 24 features (`ml/features/accel_features.py`, identical copy in `backend/app/accel_features.py`, checked by a test)
Per axis: mean, std, min, max (12). Signal magnitude vector SMV = |a|: max, min, mean, std, kurtosis, skewness (6). Dynamics: maximum jerk (|d SMV/dt|), energy (mean SMV^2). Fall-specific: std and mean deviation from 1 g in the 0.2 s after the impact peak ("is the person still moving after the hit"), share of samples with SMV < 0.6 g (free-fall), impact position in the window.
Why: falls show a free-fall dip, an impact peak and then little motion; sitting down hard or jumping have the peak but the person keeps moving.

## SisFall windowing rules (`ml/preprocessing/sisfall.py`)
Decimate 200 to 50 Hz (FIR, zero-phase), ADXL345 counts to g. ADL: sliding windows. Fall: only windows containing the impact between 10% and 90% of the window. Same rules for every class so window position cannot leak the label.

## CASAS day features (`ml/preprocessing/casas.py`)
From hourly motion counts: total, night (00-05), morning (05-12), evening (18-24), active hours, first and last active hour, hourly entropy, door events. Plus per-home typical profile and routine regularity (`ml/evaluation/eda_casas.py`).

## Pose features (`backend/app/vision.py`)
Torso angle from vertical, body aspect ratio, hip-to-knee distance over torso length, hip drop speed, movement speed, angle change, "angle bump" around 45 degrees, thigh-low indicator.

## Risk features (`backend/app/risk.py`, `features_from_signals`)
14 features: unanswered check-in hours, lateness vs the person's usual time, activity drop vs personal baseline (and daytime-only drop), missing activity data, night, fall confidence/waiting/verified/answered, SOS, missed reminders, age, drop x unanswered. The same function is used for training and serving.

## Imbalance and missing values
Class weights (`balanced`), PR-based metrics, thresholds tuned on validation data only. Missing/invalid readings are dropped at loading (counts reported by the scripts); `activity_missing` is an explicit risk feature.
