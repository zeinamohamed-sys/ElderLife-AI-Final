"""Tests the CASAS loader and baseline-comparison CODE on event logs generated here in the CASAS text format (synthetic; says nothing about real CASAS results)."""
import pathlib, tempfile, unittest
import numpy as np, pandas as pd
from ml.preprocessing import casas
from ml.training import casas_baselines as cb
def fake_home(path, seed, days=60, scale=1.0):
    rng = np.random.default_rng(seed); lines = []
    for d in range(days):
        day = pd.Timestamp("2011-03-01") + pd.Timedelta(days=d)
        for h in range(24):
            lam = scale * (0.5 if h < 6 else 6 if 7 <= h <= 21 else 2)
            for k in range(rng.poisson(lam)):
                t = day + pd.Timedelta(hours=h, minutes=int(rng.integers(0, 60)), seconds=int(rng.integers(0, 60)), microseconds=int(rng.integers(0, 999999)))
                lines.append(f"{t} M00{rng.integers(1, 6)} ON") ; lines.append(f"{t + pd.Timedelta(seconds=3)} M00{rng.integers(1, 6)} OFF")
            if rng.random() < .1: lines.append(f"{day + pd.Timedelta(hours=h, minutes=5)} D001 OPEN")
    lines += ["garbage line", "2011-03-01 25:61:00 M001 ON", lines[0]]   # unparsable + duplicate
    pathlib.Path(path).write_text("\n".join(lines))
class CasasTests(unittest.TestCase):
    def test_loader_cleans_and_builds_days(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "home1.txt"; fake_home(p, 1); ev, info = casas.parse_events(p)
            self.assertGreater(info["lines_unparsable"], 0); self.assertFalse(ev.duplicated().any())
            days, note = casas.daily_table(ev); self.assertEqual(note, ""); self.assertGreaterEqual(len(days), 55)    # first/last day dropped
            f = casas.features(days); self.assertEqual(list(f.columns), casas.FEATURES); self.assertTrue((f.total_motion > 0).all())
    def test_injection_changes_only_labelled_days(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "h.txt"; fake_home(p, 2); days, _ = casas.daily_table(casas.parse_events(p)[0]); rng = np.random.default_rng(0)
            inj, y = cb.inject(days, .2, rng); changed = (inj[cb.H].to_numpy() != days.reset_index(drop=True)[cb.H].to_numpy()).any(axis=1)
            self.assertTrue(set(np.where(changed)[0]) <= set(np.where(y == 1)[0])); self.assertEqual(int(y.sum()), int(.2 * len(days)))
    def test_leave_one_home_out_runs_and_never_uses_test_home_for_tuning(self):
        with tempfile.TemporaryDirectory() as d:
            parts = []
            for i, sc in enumerate([.6, 1.0, 1.6, 2.4]):   # homes with different activity levels (what personalisation should help with)
                p = pathlib.Path(d) / f"home{i}.txt"; fake_home(p, 10 + i, 70, sc); dd, _ = casas.daily_table(casas.parse_events(p)[0], min_events=3); dd.insert(0, "home", f"home{i}"); parts.append(dd)
            res = cb.run(pd.concat(parts, ignore_index=True), 30, .15, boots=50)
            self.assertEqual(len(res["per_home"]), 4); self.assertEqual(set(res["summary"]), {"personal", "population", "isolation_forest"})
            self.assertEqual(len(res["personal_minus_population_f1"]["bootstrap_95ci"]), 2)

class CasasEda(unittest.TestCase):
    def test_patterns_on_generated_homes(self):
        from ml.evaluation.eda_casas import home_patterns
        with tempfile.TemporaryDirectory() as d:
            parts = []
            for i, sc in enumerate([1.0, 2.0]):
                p = pathlib.Path(d) / f"h{i}.txt"; fake_home(p, 30 + i, 40, sc); dd, _ = casas.daily_table(casas.parse_events(p)[0]); dd.insert(0, "home", f"h{i}"); parts.append(dd)
            pat = home_patterns(pd.concat(parts, ignore_index=True)); self.assertEqual(set(pat), {"h0", "h1"})
            for v in pat.values(): self.assertEqual(len(v["typical_profile"]), 24); self.assertGreater(v["routine_regularity"], 0.5)   # generated homes repeat one routine
            self.assertGreater(pat["h1"]["median_daily_motion"], pat["h0"]["median_daily_motion"])
if __name__ == "__main__": unittest.main()
