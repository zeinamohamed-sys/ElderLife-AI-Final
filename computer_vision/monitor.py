"""Webcam or video file -> events for the ElderLife backend (or printed with --dry-run).
  python computer_vision/monitor.py --elderly-id 1 --source 0 --api http://localhost:8000 --device-key $DEVICE_KEY [--min-conf 0.6] [--show]
  python computer_vision/monitor.py --elderly-id 1 --source clip.mp4 --dry-run
Needs: pip install mediapipe opencv-python and the pose model (python computer_vision/download_pose_model.py).
NOT executed end-to-end in the authoring sandbox (no camera, no pose model download): the pipeline logic is tested with a fake extractor, see computer_vision/tests."""
import argparse, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import FallPipeline, iter_video_frames   # noqa: E402

def make_sink(a):
    def sink(ev):
        body = {"elderly_id": a.elderly_id, "kind": ev["kind"], "value": ev["value"]}
        if a.dry_run: print(json.dumps({**body, "activity": ev["activity"]})); return
        r = urllib.request.Request(a.api + "/events", json.dumps(body).encode(), {"Content-Type": "application/json", "X-Device-Key": a.device_key})
        try: urllib.request.urlopen(r, timeout=5).read()
        except Exception as ex: print("could not send event:", ex, file=sys.stderr)   # keep monitoring; the next event retries naturally
    return sink

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--elderly-id", type=int, required=True); ap.add_argument("--source", default="0", help="webcam index or video file")
    ap.add_argument("--api", default="http://localhost:8000"); ap.add_argument("--device-key", default=os.getenv("DEVICE_KEY", "")); ap.add_argument("--min-conf", type=float, default=float(os.getenv("FALL_MIN_CONFIDENCE", "0.6")))
    ap.add_argument("--every", type=float, default=0.2, help="seconds between analysed frames"); ap.add_argument("--cooldown", type=float, default=30, help="seconds before another fall event is sent")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--show", action="store_true"); a = ap.parse_args()
    if not a.dry_run and not a.device_key: sys.exit("--device-key (or DEVICE_KEY) is required unless --dry-run")
    from app.pose_extractor import PoseExtractor
    pipe = FallPipeline(PoseExtractor(), make_sink(a), a.min_conf, a.every, fall_cooldown_s=a.cooldown)
    try:
        for frame, t in iter_video_frames(a.source):
            res = pipe.process(frame, t)
            if a.show and res:
                import cv2; bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR); cv2.putText(bgr, f"{res['activity']} {res['confidence']:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2); cv2.imshow("ElderLife (q quits)", bgr)
                if cv2.waitKey(1) & 0xFF == ord("q"): break
    finally: print(json.dumps(pipe.stats), file=sys.stderr)
if __name__ == "__main__": main()
