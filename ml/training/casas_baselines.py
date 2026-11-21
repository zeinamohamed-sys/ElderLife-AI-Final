"""Personal vs population baseline for abnormal-day detection on CASAS home-days, evaluated with INJECTED anomalies (the datasets have no real anomaly labels).
  python -m ml.training.casas_baselines [--days ml/data/processed/casas_days.csv.gz] [--calib-days 30] [--rate 0.1] [--tag real_casas]
Design (so that the comparison is fair):
  * leave-one-home-out: the test home is never used to fit the population model or to tune any threshold;
  * all three methods get the same inputs (the 9 daily features) and the same threshold-tuning protocol (maximise F1 on the TRAINING homes' injected days);
  * personal baseline: robust z-scores (median/MAD) from the test home's own first --calib-days days (calibration days are excluded from evaluation);
  * population baseline: robust z-scores from the pooled training homes (no personalisation);  isolation forest: fitted on the training homes' days (unsupervised);
  * injected anomalies (10% of evaluation days, equal mix): inactivity (activity x0.2-0.55), night wandering (extra events 00-05h), routine shift (hourly profile rolled 5-10 h);
  * real days are assumed normal (label noise is possible); with few homes the per-home numbers are shown and the mean has a bootstrap CI over days, NOT a significance claim.
The same code runs on synthetic homes in the tests; results from those are never reported as real."""
import argparse, json, numpy as np, pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from ml.common import SEED, REPORTS
from ml.preprocessing.casas import features, FEATURES
H = [f"m{h}" for h in range(24)]; DR = [f"d{h}" for h in range(24)]
def inject(days, rate, rng):
    d = days.copy().reset_index(drop=True); y = np.zeros(len(d), int); idx = rng.choice(len(d), max(1, int(rate * len(d))), replace=False); kinds = ["inactivity", "night", "shift"]
    for i in idx:
        k = kinds[rng.integers(3)]; m = d.loc[i, H].to_numpy(float); dr = d.loc[i, DR].to_numpy(float)
        if k == "inactivity": f = rng.uniform(.2, .55); m, dr = np.round(m * f), np.round(dr * f)
        elif k == "night": m = m.copy(); m[0:5] += rng.poisson(max(m[8:20].mean(), 1) * .8, 5)
        else: s = int(rng.integers(5, 11)) * (1 if rng.random() < .5 else -1); m, dr = np.roll(m, s), np.roll(dr, s)
        d.loc[i, H], d.loc[i, DR] = m, dr; y[i] = 1
    return d, y
def robust_stats(F):
    med = F.median(); mad = (F - med).abs().median() * 1.4826; return med, mad.replace(0, np.nan).fillna(F.std().replace(0, 1)).fillna(1)
def zscore(F, med, mad): return ((F - med) / mad).clip(-10, 10)
def score(Z): return np.sqrt((Z ** 2).mean(axis=1)).to_numpy()
def tune(s, y):
    grid = np.unique(np.quantile(s, np.linspace(.5, .995, 80))); f = [precision_recall_fscore_support(y, s >= t, average="binary", zero_division=0)[2] for t in grid]; return float(grid[int(np.argmax(f))])
def prf(y, s, t):
    p, r, f, _ = precision_recall_fscore_support(y, s >= t, average="binary", zero_division=0)
    return {"precision": round(float(p), 4), "recall": round(float(r), 4), "f1": round(float(f), 4), "roc_auc": round(float(roc_auc_score(y, s)), 4) if 0 < y.sum() < len(y) else None}
def run(days, calib, rate, seed=SEED, boots=300):
    homes = sorted(days.home.unique()); assert len(homes) >= 3, "need at least 3 homes for leave-one-home-out"
    rng = np.random.default_rng(seed); per_home = {}
    prepared = {}
    for h in homes:
        d = days[days.home == h].sort_values("day").reset_index(drop=True)
        if len(d) < calib + 15: continue
        cal, ev = d.iloc[:calib], d.iloc[calib:]; evi, y = inject(ev, rate, rng); prepared[h] = (features(cal), features(evi), y, features(ev))
    for h in prepared:
        train = [k for k in prepared if k != h]; Fcal, Fev, y, _ = prepared[h]
        # population statistics + tuning data from training homes (their own calibration for personal, pooled for population)
        pool = pd.concat([prepared[k][3] for k in train]); pmed, pmad = robust_stats(pool); iso = IsolationForest(n_estimators=200, random_state=seed).fit(pool[FEATURES])
        tr_p, tr_pop, tr_iso, tr_y = [], [], [], []
        for k in train:
            cal, ev_f, yk, _ = prepared[k]; med, mad = robust_stats(cal)
            tr_p.append(score(zscore(ev_f[FEATURES], med, mad))); tr_pop.append(score(zscore(ev_f[FEATURES], pmed, pmad))); tr_iso.append(-iso.score_samples(ev_f[FEATURES])); tr_y.append(yk)
        ty = np.concatenate(tr_y); thr = {"personal": tune(np.concatenate(tr_p), ty), "population": tune(np.concatenate(tr_pop), ty), "isolation_forest": tune(np.concatenate(tr_iso), ty)}
        med, mad = robust_stats(Fcal)
        sc = {"personal": score(zscore(Fev[FEATURES], med, mad)), "population": score(zscore(Fev[FEATURES], pmed, pmad)), "isolation_forest": -iso.score_samples(Fev[FEATURES])}
        per_home[h] = {"eval_days": int(len(y)), "injected": int(y.sum()), **{m: prf(y, sc[m], thr[m]) for m in sc}, "_scores": sc, "_y": y, "_thr": thr}
    summary = {m: {"mean_f1": round(float(np.mean([v[m]["f1"] for v in per_home.values()])), 4), "mean_roc_auc": round(float(np.mean([v[m]["roc_auc"] for v in per_home.values() if v[m]["roc_auc"] is not None])), 4)} for m in ("personal", "population", "isolation_forest")}
    # bootstrap over evaluation days (pooled across homes) for the difference personal - population in F1
    brng = np.random.default_rng(seed + 1); diffs = []
    pooled = {m: np.concatenate([(v["_scores"][m] >= v["_thr"][m]) for v in per_home.values()]) for m in ("personal", "population")}; yy = np.concatenate([v["_y"] for v in per_home.values()])
    f1 = lambda pred, yv: precision_recall_fscore_support(yv, pred, average="binary", zero_division=0)[2]
    for _ in range(boots):
        i = brng.integers(0, len(yy), len(yy)); diffs.append(f1(pooled["personal"][i], yy[i]) - f1(pooled["population"][i], yy[i]))
    out = {"homes": list(per_home), "per_home": {h: {k: v for k, v in r.items() if not k.startswith("_")} for h, r in per_home.items()}, "summary": summary,
           "personal_minus_population_f1": {"point": round(float(f1(pooled["personal"], yy) - f1(pooled["population"], yy)), 4), "bootstrap_95ci": [round(float(np.quantile(diffs, .025)), 4), round(float(np.quantile(diffs, .975)), 4)],
                                            "note": "bootstrap over evaluation days of the pooled homes; days within a home are correlated, so the interval is optimistic; few homes -> treat as indicative"}}
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--days", default="ml/data/processed/casas_days.csv.gz"); ap.add_argument("--calib-days", type=int, default=30); ap.add_argument("--rate", type=float, default=.1)
    ap.add_argument("--tag", default="real_casas"); ap.add_argument("--data-kind", default="real:CASAS"); a = ap.parse_args()
    out = run(pd.read_csv(a.days), a.calib_days, a.rate); out.update(data=a.data_kind, anomalies="injected into held-out days (see module docstring); real days assumed normal")
    REPORTS.mkdir(exist_ok=True); (REPORTS / f"{a.tag}_baselines.json").write_text(json.dumps(out, indent=1)); print(json.dumps({"summary": out["summary"], "diff": out["personal_minus_population_f1"]}, indent=1))
if __name__ == "__main__": main()
