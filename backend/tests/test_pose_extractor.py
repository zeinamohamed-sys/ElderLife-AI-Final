import unittest
from types import SimpleNamespace as NS
from app.pose_extractor import landmarks_to_keypoints, IDX
from app.vision import classify_auto, sample_pose, POINTS
def fake_landmarks(kp, vis=0.9):
    lms = [NS(x=0.0, y=0.0, visibility=0.0) for _ in range(33)]
    for name, i in IDX.items(): lms[i] = NS(x=kp[name][0], y=kp[name][1], visibility=vis)
    return lms
class PoseExtractorTests(unittest.TestCase):
    def test_mapping_roundtrip_gives_same_activity(self):
        for kind in ("standing", "sitting", "lying"):
            kp = sample_pose(kind); back = landmarks_to_keypoints(fake_landmarks(kp))
            self.assertEqual(set(back), set(POINTS)); self.assertEqual(classify_auto(back)[0], classify_auto(kp)[0])
    def test_low_visibility_frame_is_dropped(self):
        self.assertIsNone(landmarks_to_keypoints(fake_landmarks(sample_pose("standing"), vis=0.2)))
if __name__ == "__main__": unittest.main()
