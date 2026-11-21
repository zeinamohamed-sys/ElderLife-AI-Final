"""Real pose estimation: image/video frame -> keypoints in the format vision.classify_auto() expects.
Uses the MediaPipe Tasks PoseLandmarker (pip install mediapipe opencv-python) with a model file you download once:
  python computer_vision/download_pose_model.py      (saves backend/app/models/pose_landmarker_lite.task)
Privacy: frames are processed in memory and never written to disk. Only keypoints (and the resulting event) leave this module.
STATUS: the landmark mapping below is unit-tested with fake landmarks; running MediaPipe itself was NOT possible in the authoring
sandbox (no network, so the .task model could not be downloaded). Test it on a machine with a webcam before relying on it."""
import os
from .vision import POINTS
# MediaPipe Pose landmark indices
IDX = {"nose": 0, "left_shoulder": 11, "right_shoulder": 12, "left_hip": 23, "right_hip": 24,
       "left_knee": 25, "right_knee": 26, "left_ankle": 27, "right_ankle": 28}
MODEL_PATH = os.getenv("POSE_MODEL_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "pose_landmarker_lite.task"))
MIN_VISIBILITY = float(os.getenv("POSE_MIN_VISIBILITY", "0.5"))   # drop frames where the body is not clearly visible

def landmarks_to_keypoints(lms, min_visibility=MIN_VISIBILITY):
    """lms: sequence of objects with .x .y .visibility (normalised image coords, y down). Returns {name: [x, y]} or None when unreliable."""
    out = {}
    for name in POINTS:
        l = lms[IDX[name]]
        if getattr(l, "visibility", 1.0) is not None and getattr(l, "visibility", 1.0) < min_visibility: return None
        out[name] = [float(l.x), float(l.y)]
    return out

class PoseExtractor:
    def __init__(self, model_path=MODEL_PATH):
        import mediapipe as mp   # imported lazily: the backend runs without it
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision as mpv
        if not os.path.exists(model_path): raise FileNotFoundError(f"Pose model missing: {model_path}. Run computer_vision/download_pose_model.py")
        self.mp = mp
        self.det = mpv.PoseLandmarker.create_from_options(mpv.PoseLandmarkerOptions(
            base_options=mpt.BaseOptions(model_asset_path=model_path), running_mode=mpv.RunningMode.IMAGE, num_poses=1))
    def keypoints(self, rgb_frame):
        """rgb_frame: HxWx3 uint8 numpy array (RGB). Returns keypoints dict or None when no person / low visibility."""
        res = self.det.detect(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb_frame))
        return landmarks_to_keypoints(res.pose_landmarks[0]) if res.pose_landmarks else None
