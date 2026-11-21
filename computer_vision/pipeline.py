"""Camera/video -> pose estimation -> keypoints -> activity/fall classification -> backend event.
Privacy: a frame is handed to the pose extractor and dropped; only the 9 keypoints (and the resulting event) are kept, and only the previous keypoints for motion.
No image or video is written anywhere. The classifier is backend/app/vision.classify_auto (trained pose model when present, rules otherwise)."""
import os, sys, time as _time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
from app.vision import classify_auto, ACTIVITY_LEVEL   # noqa: E402

class FallPipeline:
    """sink(event_dict) is called for events: {"kind": "fall"|"activity", "value": float, "activity": str}. extractor.keypoints(rgb_frame) -> dict | None."""
    def __init__(self, extractor, sink, min_conf=0.6, analyse_every_s=0.2, activity_every_s=10.0, fall_cooldown_s=30.0, max_gap_s=2.0):
        self.ex, self.sink, self.min_conf = extractor, sink, min_conf
        self.every, self.act_every, self.cooldown, self.max_gap = analyse_every_s, activity_every_s, fall_cooldown_s, max_gap_s
        self.prev, self.t_prev, self.t_last_fall, self.t_last_act = None, None, None, None
        self.stats = {"frames_seen": 0, "frames_analysed": 0, "no_person": 0, "falls_sent": 0, "activity_sent": 0}
    def process(self, frame, t):
        """Feed one RGB frame taken at time t (seconds). Returns the classification dict or None when the frame was skipped."""
        self.stats["frames_seen"] += 1
        if self.t_prev is not None and t - self.t_prev < self.every: return None
        self.stats["frames_analysed"] += 1; kp = self.ex.keypoints(frame)      # the frame is not stored anywhere
        if kp is None: self.stats["no_person"] += 1; self.prev = self.t_prev = None; return None
        dt = (t - self.t_prev) if (self.t_prev is not None and t - self.t_prev <= self.max_gap) else None
        act, conf, source = classify_auto(kp, self.prev if dt else None, dt)
        self.prev, self.t_prev = kp, t
        if act == "falling" and conf >= self.min_conf and (self.t_last_fall is None or t - self.t_last_fall >= self.cooldown):
            self.t_last_fall = t; self.stats["falls_sent"] += 1; self.sink({"kind": "fall", "value": conf, "activity": act})
        elif self.t_last_act is None or t - self.t_last_act >= self.act_every:
            self.t_last_act = t; self.stats["activity_sent"] += 1; self.sink({"kind": "activity", "value": ACTIVITY_LEVEL.get(act, 20), "activity": act})
        return {"activity": act, "confidence": conf, "source": source}

def iter_video_frames(source, max_fps=None):
    """Yields (rgb_frame, t_seconds) from a webcam index or video file with OpenCV. Needs opencv-python."""
    import cv2
    cap = cv2.VideoCapture(int(source) if str(source).isdigit() else str(source)); fps = cap.get(cv2.CAP_PROP_FPS) or 0; i = 0; t0 = _time.monotonic(); live = str(source).isdigit()
    try:
        while cap.isOpened():
            ok, bgr = cap.read()
            if not ok: break
            t = (_time.monotonic() - t0) if (live or fps <= 0) else i / fps; i += 1
            yield cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), t
    finally: cap.release()
