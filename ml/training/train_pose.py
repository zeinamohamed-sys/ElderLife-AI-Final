"""Reproducible training of the keypoint activity/fall model used by backend/app/vision.py, compared with the rule-based classifier. SYNTHETIC keypoints.
  python -m ml.training.train_pose [--install]       (--install copies the model into backend/app/models/pose_model.json)
Why synthetic: the real fall-image dataset gives single frames without motion; this model also uses motion between two frames (drop speed, angle change).
Data: 40 synthetic "people" (body scale, position, camera-tilt bias), 90 samples each over the 6 classes, with keypoint jitter, random camera tilt,
and hard cases (slowly lying down = lying, sitting down gradually = sitting, bending from standing). Split by PERSON: 24 train / 8 validation / 8 test.
Model: one-vs-rest logistic regression (repository's own pure-Python class). Numbers are NOT real-world accuracy; both the generator and the rules are ours."""
import argparse, json, math, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "backend"))
from app.mlmodels import Logistic   # noqa: E402
from app.vision import sample_pose, pose_vector, classify, POSE_CLASSES, POSE_FEATURES   # noqa: E402
from ml.common import SEED, MODELS, REPORTS   # noqa: E402

def transform(k, rng, scale, tilt, jitter=.015, dx=0.0):
    pts = np.array(list(k.values())); c = pts.mean(0); th = math.radians(tilt); R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    out = ((pts - c) * scale) @ R.T + c + np.array([dx, 0]) + rng.normal(0, jitter, pts.shape)
    return {n: [float(a), float(b)] for n, (a, b) in zip(k.keys(), out)}

def sample(kind, rng, person):
    sc, x0, tb = person; t = lambda k, **kw: transform(k, rng, sc * rng.uniform(.93, 1.07), tb + rng.normal(0, 5), **kw)
    if kind == "standing": k = t(sample_pose("standing", x0)); return k, t(sample_pose("standing", x0)), float(rng.uniform(.1, .5))
    if kind == "walking": v = rng.uniform(.5, 1.2) * .3; dt = float(rng.uniform(.1, .4)); return t(sample_pose("standing", x0)), t(sample_pose("standing", x0), dx=-v * dt * 3), dt
    if kind == "sitting":
        if rng.random() < .5: return t(sample_pose("sitting", x0)), t(sample_pose("sitting", x0)), float(rng.uniform(.1, .5))
        return t(sample_pose("sitting", x0)), t(sample_pose("standing", x0)), float(rng.uniform(1, 3))
    if kind == "bending": return t(sample_pose("bending", x0)), t(sample_pose("standing", x0)) if rng.random() < .6 else t(sample_pose("bending", x0)), float(rng.uniform(.3, 2))
    if kind == "lying":
        if rng.random() < .5: return t(sample_pose("lying", x0)), t(sample_pose("lying", x0)), float(rng.uniform(.1, .5))
        return t(sample_pose("lying", x0)), t(sample_pose("standing", x0)), float(rng.uniform(1.5, 4))   # lies down slowly on purpose
    return t(sample_pose("falling", x0) if rng.random() < .5 else sample_pose("lying", x0)), t(sample_pose("standing", x0)), float(rng.uniform(.1, .6))   # fall: fast change to the floor

def dataset(n_people=40, per=90, seed=SEED):
    rng = np.random.default_rng(seed); X, y, g, raw = [], [], [], []
    for p in range(n_people):
        person = (rng.uniform(.8, 1.2), rng.uniform(.3, .7), rng.normal(0, 4))
        for i in range(per):
            kind = POSE_CLASSES[i % len(POSE_CLASSES)]; k, prev, dt = sample(kind, rng, person)
            X.append(pose_vector(k, prev, dt)); y.append(kind); g.append(p); raw.append((k, prev, dt))
    return np.array(X), np.array(y), np.array(g), raw

def metrics(y, pred):
    acc = float((y == pred).mean()); tp = int(((pred == "falling") & (y == "falling")).sum()); fp = int(((pred == "falling") & (y != "falling")).sum()); fn = int(((pred != "falling") & (y == "falling")).sum())
    return {"accuracy": round(acc, 4), "fall_precision": round(tp / max(tp + fp, 1), 4), "fall_recall": round(tp / max(tp + fn, 1), 4), "fall_false_positives": fp, "fall_false_negatives": fn}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--install", action="store_true"); a = ap.parse_args()
    X, y, g, raw = dataset(); people = np.arange(40); rng = np.random.default_rng(SEED + 7); rng.shuffle(people); te, va = set(people[:8]), set(people[8:16])
    tr_m = np.array([p not in te and p not in va for p in g]); te_m = np.array([p in te for p in g]); assert not (set(g[tr_m]) & te)
    models = {c: Logistic(POSE_FEATURES).fit(X[tr_m].tolist(), (y[tr_m] == c).astype(int).tolist(), epochs=300) for c in POSE_CLASSES}
    pred = np.array([max(POSE_CLASSES, key=lambda c: models[c].predict(x.tolist())) for x in X[te_m]])
    rules = np.array([classify(k, prev, dt)[0] for (k, prev, dt), m in zip(raw, te_m) if m]); yt = y[te_m]
    rep = {"data": "synthetic keypoints (generator in this file)", "note": "NOT real-world evidence", "seed": SEED, "persons": {"train": int(len(set(g[tr_m]))), "val": len(va), "test": len(te)}, "test_samples": int(te_m.sum()),
           "model": metrics(yt, pred), "rules": metrics(yt, rules), "per_class_recall_model": {c: round(float((pred[yt == c] == c).mean()), 3) for c in POSE_CLASSES}, "per_class_recall_rules": {c: round(float((rules[yt == c] == c).mean()), 3) for c in POSE_CLASSES}}
    REPORTS.mkdir(exist_ok=True); MODELS.mkdir(exist_ok=True); art = {"models": {c: m.to_dict() for c, m in models.items()}, "classes": POSE_CLASSES, "metrics": {"data": "synthetic", "see": "ml/reports/synthetic_pose_metrics.json"}}
    (REPORTS / "synthetic_pose_metrics.json").write_text(json.dumps(rep, indent=1)); (MODELS / "pose_model_retrained.json").write_text(json.dumps(art, indent=1))
    if a.install: (pathlib.Path(__file__).parents[2] / "backend/app/models/pose_model.json").write_text(json.dumps(art, indent=1)); print("installed into backend")
    print(json.dumps(rep, indent=1))
if __name__ == "__main__": main()
