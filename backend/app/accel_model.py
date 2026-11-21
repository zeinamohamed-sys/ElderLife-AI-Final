"""Wearable/phone accelerometer fall model (scikit-learn pipeline trained by ml/training/train_sisfall.py).
Needs the optional packages in requirements-ml.txt (numpy, scipy, scikit-learn, joblib) and a model file at ACCEL_MODEL_PATH
(default app/models/accel_fall.joblib; copy it there with `python ml/export_to_backend.py`). The model file must be trained with the same scikit-learn version.
SAFETY: a model whose metadata says it was trained on synthetic data is REFUSED unless ALLOW_SYNTHETIC_ACCEL_MODEL=true (integration tests only)."""
import os
from app.core.logging_config import log
MODEL_PATH = os.getenv("ACCEL_MODEL_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "accel_fall.joblib"))
FS_EXPECTED = 50          # the model was trained on 50 Hz windows of 3 s (150 samples)
_state = {"loaded": False, "art": None, "reason": None}

def _allow_synthetic(): return os.getenv("ALLOW_SYNTHETIC_ACCEL_MODEL", "false").lower() == "true"

def load(force=False):
    if _state["loaded"] and not force: return _state["art"]
    _state.update(loaded=True, art=None, reason=None)
    try:
        import joblib
        if not os.path.exists(MODEL_PATH): _state["reason"] = f"model file not found: {MODEL_PATH}"; return None
        art = joblib.load(MODEL_PATH)
        data = str(art.get("data", "unknown"))
        if not data.startswith("real") and not _allow_synthetic():
            _state["reason"] = f"model data is '{data}', not real; refused (set ALLOW_SYNTHETIC_ACCEL_MODEL=true only for integration tests)"; log.warning(_state["reason"]); return None
        _state["art"] = art
    except ImportError as ex: _state["reason"] = f"optional ML packages missing: {ex}"
    except Exception as ex: _state["reason"] = f"could not load model: {ex}"; log.warning(_state["reason"])
    return _state["art"]

def info():
    art = load()
    return {"available": art is not None, "reason": _state["reason"], "data": art.get("data") if art else None,
            "threshold": art.get("threshold", 0.5) if art else None, "expected_fs_hz": FS_EXPECTED, "window_samples": FS_EXPECTED * 3}

def check_window(window):
    """Validates shape and range; returns an error string or None."""
    n = FS_EXPECTED * 3
    if not isinstance(window, list) or len(window) != n: return f"window must have exactly {n} samples (3 s at {FS_EXPECTED} Hz)"
    for r in window:
        if not isinstance(r, (list, tuple)) or len(r) != 3: return "each sample must be [x, y, z] in g"
        if any((not isinstance(v, (int, float))) or abs(v) > 16.5 or v != v for v in r): return "values must be numbers within +-16 g"
    return None

def predict_window(window):
    """window: 150 x [x, y, z] in g. Returns {"fall": bool, "probability": float, "threshold": float, "data": str} or None when no usable model."""
    art = load()
    if art is None: return None
    import numpy as np
    from app.accel_features import window_features
    p = float(art["pipeline"].predict_proba(window_features(np.asarray(window, float), FS_EXPECTED)[None])[0, 1]); thr = float(art.get("threshold", 0.5))
    return {"fall": p >= thr, "probability": round(p, 4), "threshold": round(thr, 4), "data": art.get("data")}
