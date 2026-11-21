"""Fall detection + activity recognition on REAL SisFall features (made by ml.preprocessing.sisfall).
  python -m ml.training.train_sisfall [--features ml/data/processed/sisfall_features.csv.gz] [--max-train 30000] [--fast]
Protocol (no leakage): split by SUBJECT. Adults (SA*) are split 60/20/20 into train/validation/test; SE06 (the only elderly who fell) goes to train;
the other elderly (SE*, ADL only) are split the same way. Scaler is inside the Pipeline. Hyper-parameters: GridSearchCV + GroupKFold on training
subjects (on a capped, fall-preserving subsample for speed: --max-train). Final model = best validation average precision. The alert threshold is
chosen on VALIDATION subjects (highest precision with recall >= --min-recall) and then frozen for the test subjects.
Extra honesty checks: false-alarm rate on ELDERLY ADL windows (SisFall paper reports performance drops on elderly), and per-ADL false-alarm rates.
Artefacts: ml/models/real_sisfall_fall.joblib, real_sisfall_activity.joblib, reports real_sisfall_*.json/png.  Never run in the authoring sandbox on real data."""
import argparse, json, time, joblib, numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve, f1_score, classification_report
from ml.common import SEED, MODELS, REPORTS
from ml.features.accel_features import NAMES
from ml.evaluation.plots import confusion, roc_pr

def split_subjects(df, seed=SEED):
    rng = np.random.default_rng(seed); out = {}
    ad = sorted(s for s in df.subject.unique() if s.startswith("SA")); el = sorted(s for s in df.subject.unique() if s.startswith("SE") and s != "SE06")
    for grp in (ad, el):
        rng.shuffle(grp); n = len(grp); k1, k2 = round(.6 * n), round(.8 * n)
        for i, s in enumerate(grp): out[s] = "train" if i < k1 else "val" if i < k2 else "test"
    if "SE06" in set(df.subject): out["SE06"] = "train"
    return out

def candidates(fast):
    cw = "balanced"; g = (lambda full, small: small if fast else full)
    c = {"logreg": (LogisticRegression(max_iter=3000, class_weight=cw), {"clf__C": g([0.1, 1, 10], [1])}),
         "svm_rbf": (SVC(probability=True, class_weight=cw, random_state=SEED), {"clf__C": g([1, 10], [1]), "clf__gamma": g(["scale", 0.05], ["scale"])}),
         "random_forest": (RandomForestClassifier(class_weight=cw, random_state=SEED, n_jobs=-1), {"clf__n_estimators": g([200, 400], [60]), "clf__max_depth": g([None, 14], [None])}),
         "hist_gradient_boosting": (HistGradientBoostingClassifier(class_weight=cw, random_state=SEED), {"clf__learning_rate": g([0.05, 0.1], [0.1]), "clf__max_depth": g([3, None], [3])})}
    try:
        from xgboost import XGBClassifier
        c["xgboost"] = (XGBClassifier(n_estimators=300, eval_metric="logloss", random_state=SEED, n_jobs=-1), {"clf__max_depth": g([3, 5], [3]), "clf__learning_rate": g([0.05, 0.1], [0.1])})
    except Exception: pass
    return c

def cap(df, n, rng):
    """keep every fall window, subsample ADL windows so the training frame has at most n rows (documented in the report)"""
    if len(df) <= n: return df
    f = df[df.fall == 1]; a = df[df.fall == 0]; return pd.concat([f, a.sample(max(n - len(f), 1), random_state=int(rng.integers(1e9)))])

def threshold_for_recall(y, s, min_recall):
    p, r, t = precision_recall_curve(y, s); ok = np.where(r[:-1] >= min_recall)[0]
    return float(t[ok[np.argmax(p[:-1][ok])]]) if len(ok) else float(np.min(s))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--features", default="ml/data/processed/sisfall_features.csv.gz"); ap.add_argument("--max-train", type=int, default=30000)
    ap.add_argument("--min-recall", type=float, default=0.95); ap.add_argument("--fast", action="store_true", help="tiny grids (used by tests)"); ap.add_argument("--tag", default="real_sisfall"); ap.add_argument("--data-kind", default="real:SisFall")
    a = ap.parse_args(); df = pd.read_csv(a.features); rng = np.random.default_rng(SEED)
    role = split_subjects(df); df["role"] = df.subject.map(role)
    tr, va, te = (df[df.role == r] for r in ("train", "val", "test"))
    assert not (set(tr.subject) & set(te.subject)) and not (set(tr.subject) & set(va.subject)) and not (set(va.subject) & set(te.subject)), "subject leakage"
    for nm, part in (("train", tr), ("val", va), ("test", te)):
        if part.fall.sum() == 0: raise SystemExit(f"{nm} split has no fall windows; check the data")
    trc = cap(tr, a.max_train, rng); X = lambda d: d[NAMES].to_numpy()
    report = {"task": "fall", "data": a.data_kind, "dataset": "SisFall (doi:10.3390/s17010198), ADXL345 accelerometer, 50 Hz, 3 s windows",
              "split_subjects": {k: sorted(s for s, r in role.items() if r == k) for k in ("train", "val", "test")},
              "windows": {k: {"total": int(len(d)), "fall": int(d.fall.sum())} for k, d in (("train_full", tr), ("train_used", trc), ("val", va), ("test", te))},
              "min_recall_target": a.min_recall, "models": {}}
    fitted = {}
    for name, (est, grid) in candidates(a.fast).items():
        t0 = time.time(); gs = GridSearchCV(Pipeline([("scale", StandardScaler()), ("clf", est)]), grid, cv=GroupKFold(min(4, trc.subject.nunique())), scoring="average_precision", n_jobs=-1)
        gs.fit(X(trc), trc.fall, groups=trc.subject); m = gs.best_estimator_; fitted[name] = m
        report["models"][name] = {"best_params": gs.best_params_, "cv_average_precision": round(float(gs.best_score_), 4),
                                  "val_average_precision": round(float(average_precision_score(va.fall, m.predict_proba(X(va))[:, 1])), 4), "fit_seconds": round(time.time() - t0, 1)}
    best = max(report["models"], key=lambda k: report["models"][k]["val_average_precision"]); m = fitted[best]
    thr = threshold_for_recall(va.fall.to_numpy(), m.predict_proba(X(va))[:, 1], a.min_recall)
    s = m.predict_proba(X(te))[:, 1]; pred = (s >= thr).astype(int); tp = int(((pred == 1) & (te.fall == 1)).sum()); fp = int(((pred == 1) & (te.fall == 0)).sum())
    fn = int(((pred == 0) & (te.fall == 1)).sum()); tn = int(((pred == 0) & (te.fall == 0)).sum())
    report.update(selected=best, selection_rule="highest validation average precision; threshold = best precision with validation recall >= target (frozen before touching test)", threshold=round(thr, 4),
                  test={"roc_auc": round(float(roc_auc_score(te.fall, s)), 4), "average_precision": round(float(average_precision_score(te.fall, s)), 4),
                        "recall": round(tp / max(tp + fn, 1), 4), "precision": round(tp / max(tp + fp, 1), 4), "false_alarm_rate_per_adl_window": round(fp / max(fp + tn, 1), 5),
                        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "fall_prevalence": round(float(te.fall.mean()), 4)})
    adl = te[te.fall == 0].assign(alarm=pred[(te.fall == 0).to_numpy()])
    report["false_alarms_by_adl_code"] = {c: round(float(v), 4) for c, v in adl.groupby("code").alarm.mean().sort_values(ascending=False).items()}
    el = df[(df.group == "elderly") & (df.fall == 0)]
    if len(el):   # external check on all elderly ADL windows that the model did not train on (test + validation elderly)
        el = el[el.role.isin(["val", "test"])]
        if len(el): report["elderly_adl_false_alarm_rate_val_test_subjects"] = {"windows": int(len(el)), "rate": round(float((m.predict_proba(X(el))[:, 1] >= thr).mean()), 5)}
    REPORTS.mkdir(exist_ok=True); MODELS.mkdir(exist_ok=True)
    roc_pr({k: (te.fall, fitted[k].predict_proba(X(te))[:, 1]) for k in fitted}, REPORTS / f"{a.tag}_fall_roc_pr.png", f"Fall detection, test subjects [{a.data_kind}]")
    confusion(te.fall, pred, [0, 1], REPORTS / f"{a.tag}_fall_confusion.png", f"{best} @ frozen threshold [{a.data_kind}]")
    joblib.dump({"pipeline": m, "features": NAMES, "task": "fall", "data": a.data_kind, "threshold": thr}, MODELS / f"{a.tag}_fall.joblib")
    (REPORTS / f"{a.tag}_fall_metrics.json").write_text(json.dumps(report, indent=1))
    # ---- activity recognition on ADL windows only (multi-class), same subject split
    A = df[df.fall == 0]; atr, ava, ate = (A[A.role == r] for r in ("train", "val", "test")); atrc = cap(atr.assign(fall=0), a.max_train, rng)
    ares = {"task": "activity", "data": a.data_kind, "classes": sorted(A.activity.unique()), "models": {}}; af = {}
    for name, (est, grid) in candidates(a.fast).items():
        if name == "svm_rbf": continue   # too slow for little gain at this size; keep the comparison fast
        gs = GridSearchCV(Pipeline([("scale", StandardScaler()), ("clf", est)]), grid, cv=GroupKFold(min(4, atrc.subject.nunique())), scoring="f1_macro", n_jobs=-1); gs.fit(X(atrc), atrc.activity, groups=atrc.subject)
        af[name] = gs.best_estimator_; ares["models"][name] = {"best_params": gs.best_params_, "val_macro_f1": round(float(f1_score(ava.activity, gs.best_estimator_.predict(X(ava)), average="macro")), 4)}
    ab = max(ares["models"], key=lambda k: ares["models"][k]["val_macro_f1"]); yp = af[ab].predict(X(ate))
    ares.update(selected=ab, test={"macro_f1": round(float(f1_score(ate.activity, yp, average="macro")), 4), "report": classification_report(ate.activity, yp, output_dict=True, zero_division=0)})
    confusion(ate.activity, yp, sorted(A.activity.unique()), REPORTS / f"{a.tag}_activity_confusion.png", f"Activity, {ab} [{a.data_kind}]")
    joblib.dump({"pipeline": af[ab], "features": NAMES, "task": "activity", "data": a.data_kind}, MODELS / f"{a.tag}_activity.joblib")
    (REPORTS / f"{a.tag}_activity_metrics.json").write_text(json.dumps(ares, indent=1, default=str))
    print(json.dumps({"selected": best, "threshold": report["threshold"], "test": report["test"], "activity": {"selected": ab, "macro_f1": ares["test"]["macro_f1"]}}, indent=1))
if __name__ == "__main__": main()
