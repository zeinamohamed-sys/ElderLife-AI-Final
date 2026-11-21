"""Backend accelerometer model wrapper. Uses the SYNTHETIC artefact from ml/models only to test plumbing (explicit opt-in); never a real-performance claim."""
import importlib, os, pathlib, unittest
ART = pathlib.Path(__file__).parents[2] / "ml" / "models" / "synthetic_fall.joblib"
try:
    import sklearn, joblib, numpy, scipy  # noqa
    HAVE = ART.exists()
except Exception: HAVE = False
def fresh(**env):
    for k in ("ACCEL_MODEL_PATH", "ALLOW_SYNTHETIC_ACCEL_MODEL"): os.environ.pop(k, None)
    os.environ.update(env)
    from app import accel_model; importlib.reload(accel_model); return accel_model
class AccelValidation(unittest.TestCase):
    def test_window_validation(self):
        m = fresh(); ok = [[0.0, 0.0, 1.0]] * 150
        self.assertIsNone(m.check_window(ok)); self.assertIn("exactly 150", m.check_window(ok[:10]))
        self.assertIn("[x, y, z]", m.check_window([[1, 2]] * 150)); self.assertIn("16 g", m.check_window([[0, 0, 99.0]] * 150))
        self.assertIn("16 g", m.check_window([[0, 0, float("nan")]] * 150))
    def test_missing_model_is_reported_not_crashing(self):
        m = fresh(ACCEL_MODEL_PATH="/nonexistent/model.joblib"); self.assertFalse(m.info()["available"]); self.assertIsNone(m.predict_window([[0, 0, 1.0]] * 150))
@unittest.skipUnless(HAVE, "needs numpy/scipy/scikit-learn/joblib and ml/models/synthetic_fall.joblib")
class AccelModel(unittest.TestCase):
    def test_synthetic_model_is_refused_by_default(self):
        m = fresh(ACCEL_MODEL_PATH=str(ART)); self.assertFalse(m.info()["available"]); self.assertIn("not real", m.info()["reason"])
    def test_opt_in_for_integration_tests(self):
        m = fresh(ACCEL_MODEL_PATH=str(ART), ALLOW_SYNTHETIC_ACCEL_MODEL="true"); self.assertTrue(m.info()["available"]); self.assertEqual(m.info()["data"], "synthetic")
        quiet = [[0.0, 0.7, 0.7]] * 150; fall = [[0.1, 0.2, 0.95]] * 150; fall = [list(r) for r in fall]; fall[40:46] = [[.05, .05, .1]] * 6; fall[46:49] = [[1.2, .8, 3.0]] * 3
        a, b = m.predict_window(quiet), m.predict_window(fall); self.assertLess(a["probability"], b["probability"]); self.assertIn("fall", b)
if __name__ == "__main__": unittest.main()
