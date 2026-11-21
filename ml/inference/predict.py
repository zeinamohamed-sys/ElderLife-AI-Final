"""Reproducible inference for the accelerometer models. The saved artefact holds the whole sklearn Pipeline (scaler + classifier),
so serving applies exactly the preprocessing used in training.  predict_fall(window) -> {"fall": bool, "probability": float, "data": "synthetic"|"real"}"""
import joblib
from ml.common import MODELS
from ml.features.accel_features import window_features
_cache = {}
def _load(task, tag):
    key = (task, tag)
    if key not in _cache: _cache[key] = joblib.load(MODELS / f"{tag}_{task}.joblib")
    return _cache[key]
def predict_fall(window, tag="synthetic", threshold=0.5, fs=50):
    a = _load("fall", tag); p = float(a["pipeline"].predict_proba(window_features(window, fs)[None])[0, 1])
    return {"fall": p >= threshold, "probability": round(p, 4), "data": a["data"], "model_tag": tag}
def predict_activity(window, tag="synthetic", fs=50):
    a = _load("activity", tag); return {"activity": str(a["pipeline"].predict(window_features(window, fs)[None])[0]), "data": a["data"]}
