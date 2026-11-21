"""SisFall (Sucerquia, Lopez, Vargas-Bonilla, Sensors 2017, doi:10.3390/s17010198) -> window features.
Format (from the dataset Readme): <D01-D19|F01-F15>_<SA01-SA23|SE01-SE15>_<R01-R05>.txt, 9 comma-separated columns ending with ';', 200 Hz.
Columns 1-3 = ADXL345 accelerometer (13 bit, +-16 g), 7-9 = MMA8451Q (14 bit, +-8 g). We use ADXL345:  g = raw * (2*16)/2**13.
Only SA* (adults) and SE06 performed falls; the other SE* (aged 60-75) performed ADLs only.

Windowing (identical for every class, so window position cannot leak the label):
  * recordings are decimated 200 -> 50 Hz (FIR anti-alias), windows are 3 s;
  * ADL recordings: sliding windows, stride 1.5 s, label 0;
  * fall recordings: sliding windows that contain the impact (max of |a|) between 10% and 90% of the window, label 1;
    other windows of a fall recording (before/after the fall) are dropped because their label is ambiguous.
Usage:  python -m ml.preprocessing.sisfall <SisFall_dataset_dir> [--out ml/data/processed/sisfall_features.csv.gz] [--limit-files N]
Runs ONLY on data you downloaded yourself (see ml/data/DATASETS_REGISTRY.md)."""
import argparse, io, pathlib, re
import numpy as np, pandas as pd
from scipy.signal import decimate
from ml.features.accel_features import window_features, NAMES

FS_RAW, FS, WIN_S, STRIDE_S = 200, 50, 3, 1.5
NAME_RE = re.compile(r"^([DF]\d{2})_(S[AE]\d{2})_R(\d{2})\.txt$", re.I)
ADL_GROUP = {  # activity classes for activity recognition (from the Readme's activity table)
    **dict.fromkeys(["D01", "D02"], "walking"), **dict.fromkeys(["D03", "D04"], "jogging"), **dict.fromkeys(["D05", "D06"], "stairs"),
    **dict.fromkeys(["D07", "D08", "D09", "D10"], "sit_stand"), **dict.fromkeys(["D12", "D13", "D14"], "lying_down"),
    **dict.fromkeys(["D15", "D16"], "bending"), "D17": "car_transfer",
    **dict.fromkeys(["D11", "D18", "D19"], "risky_adl")}   # collapse into chair, stumble, jump: the classic false-alarm triggers

def parse_name(fn):
    m = NAME_RE.match(fn)
    return (m.group(1).upper(), m.group(2).upper(), int(m.group(3))) if m else None

def read_accel_g(path):
    """Returns an (n, 3) float array in g (ADXL345) or None if the file is unusable."""
    txt = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore").replace(";", "")
    try: df = pd.read_csv(io.StringIO(txt), header=None, usecols=[0, 1, 2], on_bad_lines="skip")
    except Exception: return None
    x = df.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy(float) * (2 * 16 / 2 ** 13)
    x = x[(np.abs(x) <= 16.5).all(axis=1)]
    return x if len(x) >= FS_RAW * WIN_S else None

def to_50hz(x): return decimate(x, FS_RAW // FS, ftype="fir", axis=0, zero_phase=True)

def windows_of(x50, is_fall):
    W = FS * WIN_S; stride = int(FS * STRIDE_S); n = len(x50)
    if n < W: return []
    if not is_fall: return [(s, x50[s:s + W]) for s in range(0, n - W + 1, stride)]
    peak = int(np.linalg.norm(x50, axis=1).argmax()); lo, hi = max(0, peak - int(.9 * W)), min(n - W, peak - int(.1 * W))
    return [(s, x50[s:s + W]) for s in range(lo, hi + 1, stride)] if hi >= lo else []

def build(root, limit=None):
    rows, feats, skipped = [], [], []
    files = sorted(p for p in pathlib.Path(root).rglob("*.txt") if parse_name(p.name))
    if limit: files = files[:limit]
    for p in files:
        code, sub, trial = parse_name(p.name); x = read_accel_g(p)
        if x is None: skipped.append(p.name); continue
        for start, w in windows_of(to_50hz(x), code.startswith("F")):
            feats.append(window_features(w, FS)); rows.append((code, sub, trial, start, int(code.startswith("F")),
                         "fall" if code.startswith("F") else ADL_GROUP.get(code, "other"), "elderly" if sub.startswith("SE") else "adult"))
    meta = pd.DataFrame(rows, columns=["code", "subject", "trial", "start", "fall", "activity", "group"])
    return pd.concat([meta, pd.DataFrame(feats, columns=NAMES)], axis=1), skipped

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--out", default="ml/data/processed/sisfall_features.csv.gz"); ap.add_argument("--limit-files", type=int)
    a = ap.parse_args(); df, skipped = build(a.root, a.limit_files)
    if df.empty: raise SystemExit(f"no SisFall files found under {a.root} (expected files like D01_SA01_R01.txt)")
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True); df.to_csv(a.out, index=False)
    print(f"{len(df)} windows from {df.subject.nunique()} subjects ({int(df.fall.sum())} fall windows), {len(skipped)} files skipped -> {a.out}")
    if skipped: print("skipped:", skipped[:10], "..." if len(skipped) > 10 else "")
if __name__ == "__main__": main()
