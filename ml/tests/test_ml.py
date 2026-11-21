import unittest, numpy as np
from ml.common import synth_accel, FS
from ml.features.accel_features import window_features, NAMES
from ml.inference.predict import predict_fall, predict_activity
class MLTests(unittest.TestCase):
    def test_feature_vector_shape_and_finite(self):
        W, y, s = synth_accel(3, 5); f = window_features(W[0]); self.assertEqual(len(f), len(NAMES)); self.assertTrue(np.isfinite(f).all())
    def test_synthetic_has_both_classes_and_many_subjects(self):
        W, y, s = synth_accel(10, 20); self.assertIn("fall", set(y)); self.assertGreater(len(set(y)), 3); self.assertEqual(len(set(s)), 10)
    def test_subject_split_has_no_overlap(self):
        import json; d = json.load(open("ml/reports/synthetic_fall_metrics.json")); sp = d["split"]
        self.assertEqual(d["data"], "synthetic"); self.assertGreater(sp["train_subjects"] + sp["val_subjects"] + sp["test_subjects"], 0)
    def test_inference_clear_fall_vs_quiet_sitting(self):
        n = FS * 3; sit = np.tile([0.0, 0.7, 0.7], (n, 1)); fall = np.tile([0.1, 0.2, 0.95], (n, 1)).astype(float)
        fall[40:46] = [0.05, 0.05, 0.1]; fall[46:49] = [1.2, 0.8, 3.0]
        self.assertGreater(predict_fall(fall)["probability"], predict_fall(sit)["probability"])
        self.assertEqual(predict_fall(sit)["data"], "synthetic")   # artefact is labelled as synthetic
    def test_activity_returns_known_label(self):
        W, y, s = synth_accel(2, 5); self.assertIn(predict_activity(W[0])["activity"], {"walking", "standing", "sitting", "stairs", "sit_down_hard", "jumping"})
    def test_backend_feature_copy_is_identical(self):
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location("bk", pathlib.Path("backend/app/accel_features.py")); bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)
        W, y, s = synth_accel(2, 4)
        for w in W: self.assertTrue(np.allclose(window_features(w), bk.window_features(w)))
if __name__ == "__main__": unittest.main()
