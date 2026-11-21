"""Fall detection (binary) and activity recognition (multi-class) from 3 s accelerometer windows.
  python -m ml.training.train_accel                    # SYNTHETIC data (default, integration test of the pipeline)
  python -m ml.training.train_accel --real ml/data/processed/accel_windows.npz   # real windows made by ml.preprocessing.accel_real
Leakage control: split by SUBJECT (train / validation / test subjects never overlap), scaler fitted inside the Pipeline on training folds only,
hyper-parameters chosen with GroupKFold on training subjects, test set touched once. Class imbalance: class_weight='balanced'."""
import argparse, json, time, joblib, numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.metrics import classification_report, f1_score, roc_auc_score, average_precision_score, precision_score, recall_score
from ml.common import SEED, MODELS, REPORTS, synth_accel
from ml.features.accel_features import featurize, NAMES
from ml.evaluation.plots import confusion, roc_pr

def candidates(binary):
    cw = "balanced"
    return {
        "logreg": (LogisticRegression(max_iter=2000, class_weight=cw), {"clf__C": [0.1, 1, 10]}),
        "svm_rbf": (SVC(probability=True, class_weight=cw, random_state=SEED), {"clf__C": [1, 10], "clf__gamma": ["scale", 0.05]}),
        "random_forest": (RandomForestClassifier(class_weight=cw, random_state=SEED, n_jobs=-1), {"clf__n_estimators": [150, 300], "clf__max_depth": [None, 12]}),
        "gradient_boosting": (GradientBoostingClassifier(random_state=SEED), {"clf__n_estimators": [100, 200], "clf__learning_rate": [0.05, 0.1], "clf__max_depth": [2, 3]}),
    }

def run(task, X, y, g, tag, data_kind):
    subj = np.unique(g); rng = np.random.default_rng(SEED); rng.shuffle(subj)
    n = len(subj); te, va = set(subj[:int(.2 * n)]), set(subj[int(.2 * n):int(.4 * n)])
    mtr = np.array([s not in te and s not in va for s in g]); mva = np.array([s in va for s in g]); mte = np.array([s in te for s in g])
    assert not (set(g[mtr]) & set(g[mte])) and not (set(g[mtr]) & set(g[mva])), "subject leakage"
    # validation subjects are used to pick the final model; GridSearch itself uses GroupKFold inside the training subjects
    res, fitted = {}, {}
    for name, (est, grid) in candidates(task == "fall").items():
        t0 = time.time(); gs = GridSearchCV(Pipeline([("scale", StandardScaler()), ("clf", est)]), grid, cv=GroupKFold(4),
                                           scoring="f1" if task == "fall" else "f1_macro", n_jobs=-1)
        gs.fit(X[mtr], y[mtr], groups=g[mtr]); m = gs.best_estimator_
        res[name] = {"best_params": gs.best_params_, "val_f1": round(float(f1_score(y[mva], m.predict(X[mva]), average="binary" if task == "fall" else "macro", **({"pos_label": 1} if task == "fall" else {}))), 4),
                     "fit_seconds": round(time.time() - t0, 1)}; fitted[name] = m
    best = max(res, key=lambda k: res[k]["val_f1"]); m = fitted[best]; yp = m.predict(X[mte])
    out = {"task": task, "data": data_kind, "note": "SYNTHETIC data: these numbers describe the pipeline on generated windows, NOT real-world accuracy." if data_kind == "synthetic" else "real data",
           "split": {"train_subjects": int(len(set(g[mtr]))), "val_subjects": int(len(va)), "test_subjects": int(len(te)), "n_train": int(mtr.sum()), "n_test": int(mte.sum())},
           "models": res, "selected": best, "selection_rule": "highest validation F1 (validation subjects are disjoint from training and test)"}
    if task == "fall":
        s = m.predict_proba(X[mte])[:, 1]
        out["test"] = {"precision": round(float(precision_score(y[mte], yp)), 4), "recall": round(float(recall_score(y[mte], yp)), 4), "f1": round(float(f1_score(y[mte], yp)), 4),
                       "roc_auc": round(float(roc_auc_score(y[mte], s)), 4), "average_precision": round(float(average_precision_score(y[mte], s)), 4), "test_fall_prevalence": round(float(y[mte].mean()), 3)}
        roc_pr({k: (y[mte], fitted[k].predict_proba(X[mte])[:, 1]) for k in fitted}, REPORTS / f"{tag}_{task}_roc_pr.png", f"Fall detection, test subjects [{data_kind}]")
        confusion(y[mte], yp, [0, 1], REPORTS / f"{tag}_{task}_confusion.png", f"Fall vs ADL, {best} [{data_kind}]")
    else:
        out["test"] = {"macro_f1": round(float(f1_score(y[mte], yp, average="macro")), 4), "report": classification_report(y[mte], yp, output_dict=True, zero_division=0)}
        confusion(y[mte], yp, sorted(set(y)), REPORTS / f"{tag}_{task}_confusion.png", f"Activity, {best} [{data_kind}]")
    joblib.dump({"pipeline": m, "features": NAMES, "task": task, "data": data_kind}, MODELS / f"{tag}_{task}.joblib")
    (REPORTS / f"{tag}_{task}_metrics.json").write_text(json.dumps(out, indent=1, default=str)); return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--real"); a = ap.parse_args()
    if a.real:
        d = np.load(a.real, allow_pickle=True); W, lab, g = d["windows"], d["labels"].astype(str), d["subject"]; kind, tag = "real", "real"
    else: W, lab, g = synth_accel(); kind, tag = "synthetic", "synthetic"
    X = featurize(W); fall = (lab == "fall").astype(int)
    print(json.dumps({k: v for k, v in run("fall", X, fall, g, tag, kind).items() if k in ("selected", "test", "split")}, indent=1))
    adl = lab != "fall"
    r = run("activity", X[adl], lab[adl], g[adl], tag, kind); print("activity selected:", r["selected"], "macro_f1:", r["test"]["macro_f1"])
if __name__ == "__main__": main()
