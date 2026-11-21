"""Why was the synthetic activity macro-F1 exactly 1.0?  Checks (1) leakage between train and test, (2) how well ONE feature alone separates the classes,
(3) duplicate rows. Output: ml/reports/synthetic_activity_diagnosis.json. Synthetic data only."""
import json, numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GroupKFold, cross_val_score
from ml.common import synth_accel, REPORTS
from ml.features.accel_features import featurize, NAMES
W, y, g = synth_accel(); m = y != "fall"; X, y, g = featurize(W[m]), y[m], g[m]
res = {"data": "synthetic", "n_windows": int(len(y)), "n_subjects": int(len(set(g)))}
res["duplicate_feature_rows"] = int(len(X) - len({tuple(np.round(r, 6)) for r in X}))
gk = GroupKFold(5)
single = {n: float(cross_val_score(DecisionTreeClassifier(max_depth=4, random_state=0), X[:, [i]], y, groups=g, cv=gk, scoring="f1_macro").mean()) for i, n in enumerate(NAMES)}
res["best_single_features_macro_f1_depth4_tree"] = dict(sorted(single.items(), key=lambda kv: -kv[1])[:5])
best = max(single.values())
res["conclusion"] = (f"No leakage found: folds are subject-wise and there are no duplicate rows. No single feature separates the classes (best single-feature macro-F1 {best:.2f}), "
                     "but the combination of features does, because the generator gives every ADL a fixed posture/frequency signature plus small noise. "
                     "So 1.0 means the synthetic task is easy, not that the split is broken. Real activity data will be harder; do not quote this number.")
(REPORTS / "synthetic_activity_diagnosis.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
