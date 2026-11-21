"""EDA + behavioural patterns for CASAS home-days (ml/data/processed/casas_days.csv.gz from ml.preprocessing.casas).
Per home: typical hourly motion profile (median over days), weekday vs weekend totals, night-time share, and a ROUTINE REGULARITY score
(mean correlation between each day's hourly profile and the home's typical profile; 1 = same routine every day).
  python -m ml.evaluation.eda_casas [--days ...] [--tag real_casas]   ->  ml/reports/<tag>_eda_patterns.png and <tag>_eda_summary.json"""
import argparse, json, matplotlib, numpy as np, pandas as pd
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from ml.common import REPORTS
from ml.preprocessing.casas import features
H = [f"m{h}" for h in range(24)]
def home_patterns(days):
    out = {}
    for h, d in days.groupby("home"):
        M = d[H].to_numpy(float); typ = np.median(M, axis=0); f = features(d.reset_index(drop=True)); dow = pd.to_datetime(d.day).dt.dayofweek.to_numpy()
        corr = [np.corrcoef(r, typ)[0, 1] for r in M if r.std() > 0 and typ.std() > 0]
        out[h] = {"days": int(len(d)), "median_daily_motion": float(np.median(f.total_motion)), "night_share": round(float(f.night_motion.sum() / max(f.total_motion.sum(), 1)), 4),
                  "weekday_mean": round(float(f.total_motion[dow < 5].mean()), 1) if (dow < 5).any() else None, "weekend_mean": round(float(f.total_motion[dow >= 5].mean()), 1) if (dow >= 5).any() else None,
                  "routine_regularity": round(float(np.nanmean(corr)), 3) if corr else None, "typical_profile": [round(float(x), 2) for x in typ]}
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--days", default="ml/data/processed/casas_days.csv.gz"); ap.add_argument("--tag", default="real_casas"); a = ap.parse_args()
    days = pd.read_csv(a.days); pat = home_patterns(days); REPORTS.mkdir(exist_ok=True)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for h, p in pat.items(): ax[0].plot(range(24), p["typical_profile"], label=h)
    ax[0].set(title="Typical hourly motion per home (median day)", xlabel="hour of day", ylabel="motion events"); ax[0].legend(fontsize=7)
    f = features(days.reset_index(drop=True)); f["home"] = days.home.values
    f.boxplot(column="total_motion", by="home", ax=ax[1], rot=45, showfliers=False); ax[1].set(title="Daily motion events per home", xlabel="", ylabel="events/day"); plt.suptitle("")
    fig.tight_layout(); fig.savefig(REPORTS / f"{a.tag}_eda_patterns.png", dpi=110); plt.close(fig)
    s = {"homes": len(pat), "home_days": int(len(days)), "missing_values": int(days.isna().sum().sum()), "patterns": {h: {k: v for k, v in p.items() if k != "typical_profile"} for h, p in pat.items()}}
    (REPORTS / f"{a.tag}_eda_summary.json").write_text(json.dumps(s, indent=1)); print(json.dumps(s, indent=1))
if __name__ == "__main__": main()
