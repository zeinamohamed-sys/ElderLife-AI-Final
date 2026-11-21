"""Abnormal-behaviour detection on daily activity: personal baseline vs one population threshold vs Isolation Forest.
SYNTHETIC by default (labels are injected abnormal days). People are split into validation/test groups; each person's baseline comes ONLY from
their first BASE_DAYS days (robust median/MAD, so it is not leaked from the evaluated days); thresholds are tuned on validation people only."""
import json, numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from ml.common import SEED, REPORTS, synth_daily_activity
from ml.evaluation.plots import roc_pr
BASE_DAYS = 30
def prep(df):
    z, rel = [], []
    for _, p in df.groupby("person"):
        b = p.sort_values("day").iloc[:BASE_DAYS]["activity"]; med = b.median(); mad = max(1.4826 * (b - med).abs().median(), 1e-6)
        q = p[p.day >= BASE_DAYS].copy(); q["z"] = (med - q.activity) / mad; q["rel"] = q.activity / med; z.append(q)
    return __import__("pandas").concat(z)
def best_thr(s, y, grid):
    f = [precision_recall_fscore_support(y, s >= t, average="binary", zero_division=0)[2] for t in grid]; return grid[int(np.argmax(f))]
def metrics(y, s, t):
    p, r, f, _ = precision_recall_fscore_support(y, s >= t, average="binary", zero_division=0)
    return {"threshold": round(float(t), 3), "precision": round(float(p), 4), "recall": round(float(r), 4), "f1": round(float(f), 4), "roc_auc": round(float(roc_auc_score(y, s)), 4)}
def main():
    df = synth_daily_activity(); people = df.person.unique(); rng = np.random.default_rng(SEED); rng.shuffle(people)
    val_p, test_p = set(people[:10]), set(people[10:20]); train_p = set(people[20:])
    d = prep(df); va, te = d[d.person.isin(val_p)], d[d.person.isin(test_p)]
    out = {"data": "synthetic", "note": "SYNTHETIC: injected abnormal days (~5%, 20-55% of the person's usual level). Not real-world accuracy.",
           "people": {"train": len(train_p), "val": len(val_p), "test": len(test_p)}}
    # 1) personal baseline: robust z of the drop vs the person's own history
    t1 = best_thr(va.z.to_numpy(), va.abnormal.to_numpy(), np.linspace(1, 8, 36)); out["personal_baseline"] = metrics(te.abnormal.to_numpy(), te.z.to_numpy(), t1)
    # 2) population threshold: same fixed relative threshold for everyone, on raw activity value (what a person-agnostic rule would do)
    pop = -d.activity.to_numpy(); sv, st = -va.activity.to_numpy(), -te.activity.to_numpy()
    t2 = best_thr(sv, va.abnormal.to_numpy(), np.linspace(sv.min(), sv.max(), 80)); out["population_threshold"] = metrics(te.abnormal.to_numpy(), st, t2)
    # 3) Isolation Forest fitted on training people's days (no labels), features: raw activity and weekday-free relative level
    tr = d[d.person.isin(train_p)]; iso = IsolationForest(n_estimators=200, random_state=SEED).fit(tr[["activity", "rel"]])
    sv3, st3 = -iso.score_samples(va[["activity", "rel"]]), -iso.score_samples(te[["activity", "rel"]])
    t3 = best_thr(sv3, va.abnormal.to_numpy(), np.linspace(sv3.min(), sv3.max(), 80)); out["isolation_forest"] = metrics(te.abnormal.to_numpy(), st3, t3)
    roc_pr({"personal baseline": (te.abnormal, te.z), "population threshold": (te.abnormal, st), "isolation forest": (te.abnormal, st3)}, REPORTS / "synthetic_anomaly_roc_pr.png", "Abnormal days, test people [synthetic]")
    (REPORTS / "synthetic_anomaly_metrics.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
if __name__ == "__main__": main()
