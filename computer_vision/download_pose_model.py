"""Downloads the MediaPipe pose model (needs internet). Source: Google MediaPipe model card for Pose Landmarker (Apache-2.0 tooling; check the model card's terms)."""
import pathlib, urllib.request
URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
dst = pathlib.Path(__file__).parents[1] / "backend" / "app" / "models" / "pose_landmarker_lite.task"
urllib.request.urlretrieve(URL, dst); print("saved", dst, dst.stat().st_size, "bytes")
