"""Static-pose fall classifier (keypoint features from fall_images.py). Group-wise split (a group = one source video/scene), scaler inside the pipeline,
GroupKFold tuning, test groups touched once. Positive class = --positive (default 'fall').
  python -m ml.training.train_fall_images [--features ml/data/processed/fall_images_features.csv.gz] [--positive fall]
Single images carry no motion, so this model sees posture only (it cannot tell a fall in progress from lying down on purpose); the video pipeline in
backend/app/vision.py adds the temporal cues. Reports are labelled with --data-kind; the default tag is real_images."""
import argparse, json, joblib, numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score
from ml.common import SEED, MODELS, REPORTS
from ml.evaluation.plots import confusion, roc_pr
COLS = ["angle", "aspect", "hip_knee", "torso", "hip_y"]
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--features", default="ml/data/processed/fall_images_features.csv.gz"); ap.add_argument("--positive", default="fall")
    ap.add_argument("--tag", default="real_images"); ap.add_argument("--data-kind", default="real:fall-images"); a = ap.parse_args()
    df = pd.read_csv(a.features); y = (df.label == a.positive).astype(int).to_numpy(); g = df.group.to_numpy(); rng = np.random.default_rng(SEED)
    groups = np.unique(g); rng.shuffle(groups); n = len(groups)
    if n < 6: raise SystemExit(f"only {n} groups: too few for a leakage-free train/validation/test split; check --group-regex")
    te, va = set(groups[:max(1, int(.2 * n))]), set(groups[max(1, int(.2 * n)):max(2, int(.4 * n))]); role = np.array(["test" if x in te else "val" if x in va else "train" for x in g])
    tr_m, va_m, te_m = role == "train", role == "val", role == "test"
    for nm, m in (("train", tr_m), ("val", va_m), ("test", te_m)):
        if len(set(y[m])) < 2: raise SystemExit(f"{nm} split lacks one class; collect more data or change the grouping")
    X = df[COLS].to_numpy(); cw = "balanced"; res, fitted = {}, {}
    cands = {"logreg": (LogisticRegression(max_iter=2000, class_weight=cw), {"clf__C": [.1, 1, 10]}),
             "random_forest": (RandomForestClassifier(class_weight=cw, random_state=SEED), {"clf__n_estimators": [100, 300], "clf__max_depth": [None, 8]}),
             "hist_gradient_boosting": (HistGradientBoostingClassifier(class_weight=cw, random_state=SEED), {"clf__learning_rate": [.05, .1], "clf__max_depth": [3, None]})}
    for name, (est, grid) in cands.items():
        gs = GridSearchCV(Pipeline([("scale", StandardScaler()), ("clf", est)]), grid, cv=GroupKFold(min(4, len(set(g[tr_m])))), scoring="average_precision"); gs.fit(X[tr_m], y[tr_m], groups=g[tr_m]); fitted[name] = gs.best_estimator_
        res[name] = {"best_params": gs.best_params_, "val_average_precision": round(float(average_precision_score(y[va_m], gs.best_estimator_.predict_proba(X[va_m])[:, 1])), 4)}
    best = max(res, key=lambda k: res[k]["val_average_precision"]); m = fitted[best]; s = m.predict_proba(X[te_m])[:, 1]; p = (s >= .5).astype(int)
    out = {"task": "static fall posture", "data": a.data_kind, "groups": {"train": len(set(g[tr_m])), "val": len(va), "test": len(te)}, "rows": {"train": int(tr_m.sum()), "val": int(va_m.sum()), "test": int(te_m.sum())},
           "models": res, "selected": best, "test": {"precision": round(float(precision_score(y[te_m], p)), 4), "recall": round(float(recall_score(y[te_m], p)), 4), "f1": round(float(f1_score(y[te_m], p)), 4),
           "roc_auc": round(float(roc_auc_score(y[te_m], s)), 4), "average_precision": round(float(average_precision_score(y[te_m], s)), 4)}}
    roc_pr({k: (y[te_m], fitted[k].predict_proba(X[te_m])[:, 1]) for k in fitted}, REPORTS / f"{a.tag}_roc_pr.png", f"Static fall posture, test groups [{a.data_kind}]"); confusion(y[te_m], p, [0, 1], REPORTS / f"{a.tag}_confusion.png", f"{best} [{a.data_kind}]")
    joblib.dump({"pipeline": m, "features": COLS, "data": a.data_kind, "positive": a.positive}, MODELS / f"{a.tag}_fall_posture.joblib"); (REPORTS / f"{a.tag}_metrics.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
if __name__ == "__main__": main()
