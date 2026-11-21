"""Pipeline logic with a FAKE pose extractor (the real MediaPipe model cannot be downloaded offline) and a real OpenCV video file written here."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from pipeline import FallPipeline, iter_video_frames
from app.vision import sample_pose
try:
    import cv2, numpy as np; HAVE_CV = True
except Exception: HAVE_CV = False
class Fake:
    """frame is just an int index into a script of keypoints (or None = nobody in view)"""
    def __init__(self, script): self.script = script
    def keypoints(self, frame): return self.script[int(frame)]
def run(script, dts, **kw):
    ev = []; p = FallPipeline(Fake(script), ev.append, **kw); t = 0.0
    for i, dt in enumerate(dts): t += dt; p.process(i, t)
    return ev, p
class PipelineTests(unittest.TestCase):
    def test_standing_then_fall_sends_one_fall_event(self):
        script = [sample_pose("standing")] * 6 + [sample_pose("falling")] + [sample_pose("lying")] * 5; ev, p = run(script, [0.25] * len(script))
        falls = [e for e in ev if e["kind"] == "fall"]; self.assertEqual(len(falls), 1); self.assertGreaterEqual(falls[0]["value"], 0.6); self.assertEqual(p.stats["falls_sent"], 1)
    def test_repeated_fall_frames_respect_cooldown(self):
        script = [sample_pose("standing")] + [sample_pose("falling"), sample_pose("standing")] * 5; ev, _ = run(script, [0.25] * len(script), fall_cooldown_s=60)
        self.assertEqual(len([e for e in ev if e["kind"] == "fall"]), 1)
    def test_walking_or_standing_never_triggers_a_fall(self):
        script = [sample_pose("standing")] * 20; ev, _ = run(script, [0.3] * len(script)); self.assertEqual([e for e in ev if e["kind"] == "fall"], [])
    def test_activity_events_are_rate_limited(self):
        script = [sample_pose("standing")] * 40; ev, p = run(script, [0.5] * 40, activity_every_s=10); self.assertTrue(all(e["kind"] == "activity" for e in ev)); self.assertLessEqual(len(ev), 3); self.assertGreaterEqual(len(ev), 1)
    def test_frames_without_a_person_are_skipped_and_reset_motion(self):
        script = [sample_pose("standing"), None, sample_pose("lying")]; ev, p = run(script, [0.25] * 3)
        self.assertEqual(p.stats["no_person"], 1); self.assertEqual([e for e in ev if e["kind"] == "fall"], [])   # no motion pair across the gap, so lying is not a "fall"
    def test_analysis_rate_limit_and_no_frame_retention(self):
        ev = []; p = FallPipeline(Fake([sample_pose("standing")] * 20), ev.append, analyse_every_s=1.0)
        for i in range(20): p.process(i, i * 0.1)
        self.assertEqual(p.stats["frames_seen"], 20); self.assertLessEqual(p.stats["frames_analysed"], 3)
        for e in ev: self.assertEqual(set(e), {"kind", "value", "activity"})          # events carry numbers/labels only, never pixels
        self.assertFalse([v for v in vars(p).values() if hasattr(v, "shape")])        # the pipeline holds no image arrays
    @unittest.skipUnless(HAVE_CV, "opencv not installed")
    def test_video_file_is_read_and_processed(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "clip.avi"); w = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
            for i in range(30): w.write(np.full((48, 64, 3), i * 8 % 255, np.uint8))
            w.release(); frames = list(iter_video_frames(path)); self.assertEqual(len(frames), 30); self.assertEqual(frames[0][0].shape, (48, 64, 3)); self.assertAlmostEqual(frames[10][1], 1.0, places=2)
            script = [sample_pose("standing")] * 15 + [sample_pose("falling")] + [sample_pose("lying")] * 14; ev = []; p = FallPipeline(Fake(script), ev.append, analyse_every_s=0.05)
            for i, (_, t) in enumerate(frames): p.process(i, t)      # extractor ignores the pixels and uses the frame index
            self.assertEqual(len([e for e in ev if e["kind"] == "fall"]), 1)
if __name__ == "__main__": unittest.main()
