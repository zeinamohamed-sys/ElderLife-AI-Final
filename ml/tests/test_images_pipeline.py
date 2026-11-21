"""Image pipeline code on IMAGES GENERATED HERE (random noise / drawings). Pose estimation itself is not run (no MediaPipe model offline)."""
import pathlib, subprocess, sys, tempfile, unittest, os, json
import numpy as np, pandas as pd
try:
    import cv2; HAVE_CV = True
except Exception: HAVE_CV = False
from ml.preprocessing import fall_images as fi
from app.vision import sample_pose
class ImagePipeline(unittest.TestCase):
    def test_group_names(self):
        self.assertEqual(fi.group_of("video3_frame0042_jpg.rf.abcdef0123"), "video3"); self.assertEqual(fi.group_of("scene_a_12"), "scene_a"); self.assertEqual(fi.group_of("x7", r"^(x)\d+$"), "x")
    @unittest.skipUnless(HAVE_CV, "opencv not installed")
    def test_scan_validates_dedupes_and_labels(self):
        rng = np.random.default_rng(0)
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d); (d / "train" / "fall").mkdir(parents=True); (d / "train" / "standing").mkdir(); a = rng.integers(0, 255, (96, 96, 3), dtype=np.uint8)
            cv2.imwrite(str(d / "train/fall/v1_1.jpg"), a); cv2.imwrite(str(d / "train/fall/v1_2.png"), a)                       # exact duplicate content
            cv2.imwrite(str(d / "train/standing/v2_1.jpg"), rng.integers(0, 255, (96, 96, 3), dtype=np.uint8)); cv2.imwrite(str(d / "train/standing/tiny.jpg"), a[:10, :10])
            (d / "train/standing/broken.jpg").write_bytes(b"not an image")
            df, rej = fi.scan(d, {0: "fall", 1: "standing"}); self.assertEqual(rej["duplicate"], 1); self.assertEqual(rej["too_small"], 1); self.assertEqual(rej["unreadable"], 1)
            self.assertEqual(sorted(df.label), ["fall", "standing"]); self.assertTrue((df.group.isin(["v1", "v2"])).all())
    def test_feature_row_separates_lying_from_standing(self):
        up, lie = fi.feature_row(sample_pose("standing")), fi.feature_row(sample_pose("lying")); self.assertLess(up["angle"], 20); self.assertGreater(lie["angle"], 60)
    def test_training_script_on_generated_features_is_group_split(self):
        rng = np.random.default_rng(1); rows = []
        for gi in range(12):
            for k in range(10):
                lab = "fall" if gi % 2 == 0 else "standing"; kp = sample_pose("lying" if lab == "fall" else "standing", x=float(rng.uniform(.3, .7)))
                kp = {n: [v[0] + rng.normal(0, .02), v[1] + rng.normal(0, .02)] for n, v in kp.items()}; rows.append({"label": lab, "group": f"g{gi}", **fi.feature_row(kp)})
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "f.csv.gz"; pd.DataFrame(rows).to_csv(f, index=False)
            r = subprocess.run([sys.executable, "-m", "ml.training.train_fall_images", "--features", str(f), "--tag", "unittest_img", "--data-kind", "synthetic-keypoints"], capture_output=True, text=True, env=dict(os.environ, PYTHONWARNINGS="ignore"), cwd=pathlib.Path(__file__).parents[2])
            self.assertEqual(r.returncode, 0, r.stderr[-1500:]); rep = json.loads(r.stdout); self.assertEqual(rep["data"], "synthetic-keypoints"); self.assertEqual(sum(rep["groups"].values()), 12)
            for sub in ("reports", "models"):
                for p in (pathlib.Path(__file__).parents[1] / sub).glob("unittest_img*"): p.unlink()
if __name__ == "__main__": unittest.main()
