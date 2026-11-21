"""COPY of ml/features/accel_features.py (the backend image does not contain ml/); ml/tests/test_ml.py checks both give identical output. Hand-crafted features for one accelerometer window (T x 3, in g). The same function is used for training and serving."""
import numpy as np
from scipy.stats import kurtosis, skew
NAMES = [f"{a}_{b}" for a in "xyz" for b in ("mean", "std", "min", "max")] + [
    "smv_max", "smv_min", "smv_mean", "smv_std", "smv_kurt", "smv_skew", "jerk_max", "energy",
    "post_peak_std", "post_peak_mean_dev", "freefall_frac", "peak_pos"]
def window_features(w, fs=50):
    w = np.asarray(w, float); smv = np.linalg.norm(w, axis=1); f = []
    for a in range(3): f += [w[:, a].mean(), w[:, a].std(), w[:, a].min(), w[:, a].max()]
    pk = int(smv.argmax()); post = smv[min(pk + fs // 5, len(smv) - 1):]
    jerk = np.abs(np.diff(smv)) * fs
    f += [smv.max(), smv.min(), smv.mean(), smv.std(), kurtosis(smv), skew(smv), jerk.max(), float((smv ** 2).mean()),
          post.std() if len(post) > 1 else 0.0, abs(post.mean() - 1.0) if len(post) else 0.0, float((smv < 0.6).mean()), pk / len(smv)]
    return np.nan_to_num(np.array(f))
def featurize(windows, fs=50): return np.vstack([window_features(w, fs) for w in windows])
