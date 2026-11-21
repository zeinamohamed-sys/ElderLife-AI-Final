"""Fall-image dataset -> pose-keypoint feature table (privacy: only keypoint features are kept; images are read and never copied).
Layouts understood:  (a) <root>/<split>/<class_name>/*.jpg   (b) YOLO: <root>/<split>/images/*.jpg + <root>/<split>/labels/*.txt  (use --classes "0:fall,1:standing,...").
Steps: 1) validate (cv2 can decode, min size)  2) drop exact/near duplicates (average hash)  3) assign a GROUP per source video/scene from the file name
(so near-identical frames never land in both train and test)  4) extract 9 keypoints with MediaPipe PoseLandmarker (needs the .task model, computer_vision/download_pose_model.py)
5) write ml/data/processed/fall_images_features.csv.gz.  Run: python -m ml.preprocessing.fall_images <root> --classes "0:fall,1:standing"
Needs opencv-python and mediapipe. Steps 1-3 and the feature computation are unit-tested on generated images; step 4 needs the model file and was NOT run here."""
import argparse, json, pathlib, re, sys
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "backend"))
from app.vision import features as pose_features, POINTS   # noqa: E402
IMG = {".jpg", ".jpeg", ".png", ".bmp"}
def group_of(stem, regex=None):
    """Roboflow-style names 'video3_frame0042_jpg.rf.<hash>' -> 'video3'; override with --group-regex (first group = id)."""
    if regex:
        m = re.match(regex, stem); return m.group(1) if m else stem
    s = re.sub(r"_(jpg|jpeg|png)\.rf\.[0-9a-f]+$", "", stem); s = re.sub(r"[-_ ]?(frame|img|image)?[-_ ]?\d+$", "", s, flags=re.I); return s or stem
def ahash(img, size=8):
    import cv2
    g = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img, (size, size), interpolation=cv2.INTER_AREA).astype(float); return "".join("1" if v else "0" for v in (g > g.mean()).ravel())
def hamming(a, b): return sum(x != y for x, y in zip(a, b))
def read_label(path, root, classes):
    p = pathlib.Path(path)
    if p.parent.name in set(classes.values()): return p.parent.name                 # layout (a)
    lab = p.parent.parent / "labels" / (p.stem + ".txt")                              # layout (b)
    if lab.exists():
        ids = [int(l.split()[0]) for l in lab.read_text().splitlines() if l.strip()]
        if ids: return classes.get(max(set(ids), key=ids.count), f"class{ids[0]}")
    return None
def scan(root, classes, group_regex=None, min_size=64, dup_dist=2):
    import cv2
    rows, rejected, seen = [], {"unreadable": 0, "too_small": 0, "no_label": 0, "duplicate": 0}, []
    for p in sorted(pathlib.Path(root).rglob("*")):
        if p.suffix.lower() not in IMG: continue
        img = cv2.imread(str(p))
        if img is None: rejected["unreadable"] += 1; continue
        if min(img.shape[:2]) < min_size: rejected["too_small"] += 1; continue
        lab = read_label(p, root, classes)
        if lab is None: rejected["no_label"] += 1; continue
        h = ahash(img)
        if any(hamming(h, o) <= dup_dist for o in seen): rejected["duplicate"] += 1; continue
        seen.append(h); rows.append({"path": str(p), "label": lab, "group": group_of(p.stem, group_regex), "ahash": h})
    return pd.DataFrame(rows), rejected
def feature_row(kp):
    f = pose_features(kp); return {"angle": f["angle"], "aspect": f["aspect"], "hip_knee": f["hip_knee"], "torso": f["torso"], "hip_y": f["hip"][1]}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--classes", default="0:fall,1:standing"); ap.add_argument("--group-regex")
    ap.add_argument("--out", default="ml/data/processed/fall_images_features.csv.gz"); a = ap.parse_args()
    classes = {int(k): v for k, v in (c.split(":") for c in a.classes.split(","))}; df, rej = scan(a.root, classes, a.group_regex)
    if df.empty: raise SystemExit("no usable images: " + json.dumps(rej))
    import cv2; from app.pose_extractor import PoseExtractor
    px = PoseExtractor(); keep, nopose = [], 0
    for _, r in df.iterrows():
        kp = px.keypoints(cv2.cvtColor(cv2.imread(r.path), cv2.COLOR_BGR2RGB))
        if kp is None: nopose += 1; continue
        keep.append({"label": r.label, "group": r.group, **feature_row(kp)})
    out = pd.DataFrame(keep); pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True); out.to_csv(a.out, index=False)
    print(json.dumps({"images_scanned_ok": int(len(df)), "rejected": rej, "no_person_detected": nopose, "rows": int(len(out)), "groups": int(out.group.nunique()), "labels": out.label.value_counts().to_dict()}, indent=1))
if __name__ == "__main__": main()
