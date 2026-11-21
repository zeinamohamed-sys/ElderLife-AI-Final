"""Rebuilds backend/app/models/metrics.json (shown on the Analytics page) ONLY from reproducible reports in ml/reports/.
Run the trainers first:  python -m ml.training.train_risk ; train_pose ; train_anomaly   then   python ml/export_metrics.py
Every value is synthetic-data, and the file says so."""
import json, pathlib
R = pathlib.Path(__file__).parent / "reports"; load = lambda n: json.loads((R / n).read_text())
risk, pose, an = load("synthetic_risk_metrics.json"), load("synthetic_pose_metrics.json"), load("synthetic_anomaly_metrics.json")
out = {"risk": {"auc": {"model": risk["hybrid_model_plus_safety_floor"]["roc_auc"], "rules": risk["rules"]["roc_auc"]},
                "average_precision": {"model": risk["hybrid_model_plus_safety_floor"]["average_precision"], "rules": risk["rules"]["average_precision"]},
                "high_plus_alerts": {"model": risk["hybrid_model_plus_safety_floor"], "rules": risk["rules"]}, "prevalence": risk["prevalence_test"]},
       "pose": {"model_accuracy": pose["model"]["accuracy"], "rules_accuracy": pose["rules"]["accuracy"],
                "fall_model": {"precision": pose["model"]["fall_precision"], "recall": pose["model"]["fall_recall"]}, "fall_rules": {"precision": pose["rules"]["fall_precision"], "recall": pose["rules"]["fall_recall"]}},
       "anomaly": {"personal_baseline": {k: an["personal_baseline"][k] for k in ("f1", "precision", "recall")}, "population_threshold": {k: an["population_threshold"][k] for k in ("f1", "precision", "recall")}},
       "data": "synthetic", "reproduce": "ml/training/train_risk.py, train_pose.py, train_anomaly.py (seed 42); see docs/MODEL_EVALUATION.md"}
(pathlib.Path(__file__).parents[1] / "backend/app/models/metrics.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1)[:700])
