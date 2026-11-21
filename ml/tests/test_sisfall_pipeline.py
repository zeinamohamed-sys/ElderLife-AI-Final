"""Tests the SisFall loader/EDA/training CODE on files that are WRITTEN IN THE SisFall FORMAT BUT GENERATED HERE (synthetic).
They prove the parser, windowing rules, split and scripts work; they say nothing about accuracy on the real dataset."""
import json, os, pathlib, subprocess, sys, tempfile, unittest
import numpy as np
from ml.preprocessing import sisfall
def write_file(path, g, rng):
    raw = np.round(g / (2 * 16 / 2 ** 13)).astype(int); n = len(raw)
    cols = np.hstack([raw, rng.integers(-5, 5, (n, 3)), raw])   # 9 columns like the real files
    pathlib.Path(path).write_text("\n".join(",".join(map(str, r)) + ";" for r in cols))
def fake_dataset(root, seed=0):
    rng = np.random.default_rng(seed); subs = [f"SA{i:02d}" for i in range(1, 11)] + ["SE01", "SE02", "SE03", "SE06"]
    for s in subs:
        d = pathlib.Path(root) / s; d.mkdir(parents=True)
        for code in ("D01", "D07", "D11", "D19", "F01", "F10") if s.startswith("SA") or s == "SE06" else ("D01", "D07", "D11"):
            for r in (1, 2):
                n = 200 * (20 if code.startswith("D01") else 12); t = np.arange(n) / 200; g = np.zeros((n, 3)); g[:, 2] = 1
                if code == "D01": g[:, 2] += .35 * np.sin(2 * np.pi * 1.8 * t)
                elif code == "D07": i = n // 3; g[i:i + 40, 2] += .6; g[i + 40:, 1] += .6
                elif code in ("D11", "D19"): i = n // 2; g[i:i + 10, 2] += rng.uniform(1.5, 2.5)
                else:
                    i = n // 3; g[i:i + 30] *= .3; g[i + 30:i + 40, 2] += rng.uniform(2, 3.5); g[i + 40:] = [.9, .2, .1]
                write_file(d / f"{code}_{s}_R{r:02d}.txt", g + rng.normal(0, .03, g.shape), rng)
class SisFallTests(unittest.TestCase):
    def test_name_and_unit_conversion(self):
        self.assertEqual(sisfall.parse_name("F05_SA01_R04.txt"), ("F05", "SA01", 4)); self.assertIsNone(sisfall.parse_name("readme.txt"))
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "D01_SA01_R01.txt"; p.write_text("\n".join(["0,256,0,1,2,3,0,0,0;"] * 700))   # 256 counts = 1.0 g
            x = sisfall.read_accel_g(p); self.assertAlmostEqual(float(x[0, 1]), 1.0, places=6)
    def test_fall_windows_contain_the_impact_and_adl_windows_slide(self):
        x = np.zeros((300, 3)); x[:, 2] = 1; x[120:123, 2] = 4
        ws = sisfall.windows_of(x, True); self.assertTrue(ws)
        for s, w in ws: self.assertTrue(.1 * 150 <= 120 - s <= .9 * 150)   # peak inside 10-90% of every fall window
        self.assertEqual(len(sisfall.windows_of(x, False)), (300 - 150) // 75 + 1)
    def test_end_to_end_on_generated_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d) / "sis"; fake_dataset(root); df, skipped = sisfall.build(root)
            self.assertEqual(skipped, []); self.assertGreater(df.fall.sum(), 10); self.assertGreater((df.fall == 0).sum(), 50); self.assertEqual(df.isna().sum().sum(), 0)
            self.assertTrue(set(df[df.fall == 1].subject) <= {f"SA{i:02d}" for i in range(1, 11)} | {"SE06"})
            f = pathlib.Path(d) / "feat.csv.gz"; df.to_csv(f, index=False); env = dict(os.environ, PYTHONWARNINGS="ignore")
            r = subprocess.run([sys.executable, "-m", "ml.training.train_sisfall", "--features", str(f), "--fast", "--tag", "unittest_tmp", "--data-kind", "synthetic-in-SisFall-format"], capture_output=True, text=True, env=env, cwd=pathlib.Path(__file__).parents[2])
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            rep = json.load(open(pathlib.Path(__file__).parents[1] / "reports" / "unittest_tmp_fall_metrics.json"))
            self.assertFalse(set(rep["split_subjects"]["train"]) & set(rep["split_subjects"]["test"]))
            self.assertEqual(rep["data"], "synthetic-in-SisFall-format")
            for p in (pathlib.Path(__file__).parents[1] / "reports").glob("unittest_tmp_*"): p.unlink()
            for p in (pathlib.Path(__file__).parents[1] / "models").glob("unittest_tmp_*"): p.unlink()
if __name__ == "__main__": unittest.main()
