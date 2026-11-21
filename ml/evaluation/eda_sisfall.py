"""EDA for SisFall features (ml/data/processed/sisfall_features.csv.gz): class balance, subjects, per-activity impact strength, elderly vs adults.
  python -m ml.evaluation.eda_sisfall [--features ...] [--tag real_sisfall]   ->  ml/reports/<tag>_eda_*.png and <tag>_eda_summary.json (+ docs/EDA_REPORT.md section)"""
import argparse, json, matplotlib, pandas as pd
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from ml.common import REPORTS
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--features", default="ml/data/processed/sisfall_features.csv.gz"); ap.add_argument("--tag", default="real_sisfall"); a = ap.parse_args()
    df = pd.read_csv(a.features); REPORTS.mkdir(exist_ok=True)
    s = {"windows": int(len(df)), "subjects": int(df.subject.nunique()), "fall_windows": int(df.fall.sum()), "fall_fraction": round(float(df.fall.mean()), 4),
         "missing_values": int(df.isna().sum().sum()), "windows_by_group": df.group.value_counts().to_dict(), "falls_by_group": df[df.fall == 1].group.value_counts().to_dict(),
         "windows_per_activity": df.activity.value_counts().to_dict(), "smv_max_median_by_class": df.groupby("fall").smv_max.median().round(3).to_dict()}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    df.activity.value_counts().plot.barh(ax=ax[0], title="Windows per activity class"); ax[0].set_xscale("log")
    df.boxplot(column="smv_max", by="code", ax=ax[1], rot=90, showfliers=False); ax[1].set(title="Peak acceleration (g) per SisFall activity", xlabel="", ylabel="max |a| (g)"); plt.sca(ax[1]); plt.suptitle("")
    for g, d in df.groupby("group"): ax[2].hist(d[d.fall == 0].smv_max.clip(upper=6), bins=40, alpha=.5, density=True, label=f"{g} ADL")
    ax[2].hist(df[df.fall == 1].smv_max.clip(upper=6), bins=40, alpha=.5, density=True, label="falls"); ax[2].legend(); ax[2].set(title="Peak acceleration: ADL vs falls", xlabel="max |a| (g, clipped at 6)")
    fig.tight_layout(); fig.savefig(REPORTS / f"{a.tag}_eda_overview.png", dpi=110); plt.close(fig)
    (REPORTS / f"{a.tag}_eda_summary.json").write_text(json.dumps(s, indent=1, default=str)); print(json.dumps(s, indent=1, default=str))
if __name__ == "__main__": main()
