"""Reproducible risk-model training and comparison against the hand-written rules. SYNTHETIC scenarios only.
  python -m ml.training.train_risk [--install]      (--install copies the result into backend/app/models/risk_model.json; default is NOT to touch the backend)
Why synthetic: no dataset with real "this person was in danger" labels exists in this project. The scenarios below are generated from named situations
(normal day, benign slow day, fall answered/unanswered, incapacitated, SOS, false SOS-free noise) with label noise, so the labels are NOT computed by the rules
that are being compared. Even so, both the generator and the rules were written by the same authors: the numbers show the pipeline works and how the hybrid
behaves in these scenarios, they are NOT evidence of real-world benefit. The model is the repository's own pure-Python logistic regression (app/mlmodels.py);
the safety floor in app/risk.py (SOS => Critical, unanswered verified fall => High) is part of the hybrid and is never learned away.
Splits: train / validation (threshold tuning) / test, different seeds, no scenario shared."""
import argparse, json, pathlib, sys
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve
sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "backend"))
from app.mlmodels import Logistic   # noqa: E402
from app.risk import FEATURES, features_from_signals, assess_rules, ml_level_index, LEVELS   # noqa: E402
from ml.common import SEED, MODELS, REPORTS   # noqa: E402

def scenario(rng):
    """returns (signals, label). label 1 = the person needs a human to act now."""
    k = rng.choice(["normal", "slow_day", "late_checkin", "fall_answered", "fall_unanswered", "incapacitated", "sos", "inactive_long"], p=[.575, .12, .10, .04, .035, .035, .02, .075])
    usual = float(rng.choice([10.0, 30.0, 60.0])) if rng.random() < .8 else None
    s = {"checkin_delay_min": float(rng.uniform(0, 25)), "checkin_responded": True, "checkin_usual_min": usual, "activity_ratio": float(np.clip(rng.normal(1.0, .25), .2, 2)),
         "fall": False, "fall_answered": False, "fall_age_s": 0, "verify_s": 60, "sos": False, "missed_reminders": int(rng.choice([0, 0, 0, 1, 2])), "hour": int(rng.integers(0, 24)),
         "fall_conf": 1.0, "age": int(rng.integers(65, 96))}; y = 0
    if k == "slow_day": s["activity_ratio"] = float(rng.uniform(.3, .6))
    elif k == "late_checkin": s["checkin_delay_min"] = float(rng.uniform(40, 200)); s["checkin_responded"] = bool(rng.random() < .7)
    elif k == "fall_answered": s.update(fall=True, fall_answered=True, fall_conf=float(rng.uniform(.6, 1)), fall_age_s=int(rng.integers(5, 300)))
    elif k == "fall_unanswered": s.update(fall=True, fall_answered=False, fall_conf=float(rng.uniform(.6, 1)), fall_age_s=int(rng.integers(0, 400)), checkin_responded=False, checkin_delay_min=float(rng.uniform(0, 120))); y = int(s["fall_age_s"] >= s["verify_s"])   # product policy: ask the person first; a human is needed only after the verification window
    elif k == "incapacitated": s.update(checkin_responded=False, checkin_delay_min=float(rng.uniform(90, 400)), activity_ratio=float(rng.uniform(0, .4))); y = 1
    elif k == "sos": s["sos"] = True; y = 1
    elif k == "inactive_long": s.update(checkin_responded=False, checkin_delay_min=float(rng.uniform(100, 360)), activity_ratio=float(rng.uniform(.0, .5)), missed_reminders=int(rng.integers(1, 4))); y = int(rng.random() < .45)
    if rng.random() < .03: y = 1 - y     # label noise
    return s, y

def make(n, seed):
    rng = np.random.default_rng(seed); S, Y = zip(*(scenario(rng) for _ in range(n))); return list(S), np.array(Y)

def evaluate(name, S, y, level_idx, score):
    alert = level_idx >= 3; tp = int((alert & (y == 1)).sum()); fp = int((alert & (y == 0)).sum()); fn = int((~alert & (y == 1)).sum()); tn = int((~alert & (y == 0)).sum())
    return {"roc_auc": round(float(roc_auc_score(y, score)), 4), "average_precision": round(float(average_precision_score(y, score)), 4), "alerts_high_plus": tp + fp, "tp": tp, "fp": fp, "fn": fn,
            "precision": round(tp / max(tp + fp, 1), 4), "recall": round(tp / max(tp + fn, 1), 4), "false_alerts_per_1000_scenarios": round(1000 * fp / len(y), 1)}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--install", action="store_true"); ap.add_argument("--n-train", type=int, default=8000); a = ap.parse_args()
    Str, ytr = make(a.n_train, SEED); Sva, yva = make(4000, SEED + 1); Ste, yte = make(8000, SEED + 2)
    X = lambda S: [features_from_signals(s) for s in S]
    m = Logistic(FEATURES).fit(X(Str), ytr.tolist(), epochs=250)
    pva = np.array([m.predict(x) for x in X(Sva)]); p, r, t = precision_recall_curve(yva, pva); f1 = 2 * p * r / np.maximum(p + r, 1e-9); high = float(t[int(np.argmax(f1[:-1]))])
    neg = pva[yva == 0]   # "low" = a score that only 5% of validation days that were fine reach, so a quiet day is "Normal"
    low = min(float(np.quantile(neg, .95)), high); medium = float(np.sqrt(low * high))   # medium: geometric middle between low and the F1-optimal high threshold
    thr = {"low": round(low, 4), "medium": round(medium, 4), "high": round(high, 4), "critical": round(min(.999, high * 1.2), 4)}
    pte = np.array([m.predict(x) for x in X(Ste)]); idx = np.array([ml_level_index(float(p_), thr, s)[0] for p_, s in zip(pte, Ste)])
    rules = [assess_rules({**s}) for s in Ste]; ridx = np.array([LEVELS.index(r["level"]) for r in rules]); rscore = np.array([r["score"] for r in rules])
    floor = np.array([ml_level_index(0.0, thr, s)[1] for s in Ste]); hscore = np.maximum(pte, np.where(floor == 4, .7, np.where(floor == 3, .4, 0)))
    rep = {"data": "synthetic scenarios (generator in this file), label noise 3%", "note": "NOT real-world evidence: see module docstring", "seed": SEED,
           "sizes": {"train": len(ytr), "val": len(yva), "test": len(yte)}, "prevalence_test": round(float(yte.mean()), 4), "thresholds": thr,
           "rules": evaluate("rules", Ste, yte, ridx, rscore), "model_only": evaluate("model", Ste, yte, (pte >= high).astype(int) * 3, pte), "hybrid_model_plus_safety_floor": evaluate("hybrid", Ste, yte, idx, hscore),
           "feature_weights": dict(zip(FEATURES, [round(w, 3) for w in m.w]))}
    REPORTS.mkdir(exist_ok=True); MODELS.mkdir(exist_ok=True)
    (REPORTS / "synthetic_risk_metrics.json").write_text(json.dumps(rep, indent=1))
    art = {"model": m.to_dict(), "thresholds": thr, "metrics": {"data": "synthetic", "see": "ml/reports/synthetic_risk_metrics.json"}}
    (MODELS / "risk_model_retrained.json").write_text(json.dumps(art, indent=1))
    if a.install: (pathlib.Path(__file__).parents[2] / "backend" / "app" / "models" / "risk_model.json").write_text(json.dumps(art, indent=1)); print("installed into backend")
    print(json.dumps({k: rep[k] for k in ("prevalence_test", "thresholds", "rules", "model_only", "hybrid_model_plus_safety_floor")}, indent=1))
if __name__ == "__main__": main()
