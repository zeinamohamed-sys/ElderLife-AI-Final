"""Loader for a REAL accelerometer fall dataset laid out as <root>/**/*.csv|txt, one recording per file.
NOT EXECUTED here: the dataset is not in this repository. Edit COLUMNS / SUBJECT_REGEX / label_from_path for the dataset your team
downloaded, then run:  python -m ml.preprocessing.accel_real <root> --fs 50
Cleaning: drop NaN/inf rows, clip to +-16 g, 3 s windows with 50% overlap (no resampling: pass the dataset's rate in --fs).
Output: ml/data/processed/accel_windows.npz (windows, labels, subject)."""
import argparse, pathlib, re, numpy as np, pandas as pd
COLUMNS = ["ax", "ay", "az"]                    # EDIT: accelerometer columns (units must be g)
SUBJECT_REGEX = r"(?:S|sub|subject)[_-]?(\d+)"  # EDIT
def label_from_path(p: pathlib.Path) -> str:    # EDIT: map folder/file naming to "fall" or an activity name
    return "fall" if "fall" in str(p).lower() else "adl"
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--fs", type=int, default=50); a = ap.parse_args()
    W, y, s = [], [], []; n = a.fs * 3; skipped = 0
    for f in sorted(pathlib.Path(a.root).rglob("*")):
        if f.suffix.lower() not in (".csv", ".txt"): continue
        try: df = pd.read_csv(f, usecols=COLUMNS)
        except Exception: skipped += 1; continue
        x = df.replace([np.inf, -np.inf], np.nan).dropna().clip(-16, 16).to_numpy(float)
        m = re.search(SUBJECT_REGEX, f.name, re.I); sub = int(m.group(1)) if m else -1
        for i in range(0, len(x) - n + 1, n // 2): W.append(x[i:i + n]); y.append(label_from_path(f)); s.append(sub)
    out = pathlib.Path(__file__).parents[1] / "data" / "processed" / "accel_windows.npz"
    np.savez_compressed(out, windows=np.array(W), labels=np.array(y), subject=np.array(s)); print(len(W), "windows,", skipped, "files skipped ->", out)
if __name__ == "__main__": main()
