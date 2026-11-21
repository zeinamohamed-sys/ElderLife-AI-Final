# Computer vision pipeline

```
camera / video file --(OpenCV)--> RGB frame --(MediaPipe PoseLandmarker)--> 9 keypoints
   --> features (torso angle, aspect, hip drop speed...) --> classify_auto (trained pose model, rules as fallback)
   --> walking / standing / sitting / bending / lying / falling --> POST /events (X-Device-Key) --> verify-then-escalate alert flow
```
Code: `computer_vision/pipeline.py` (logic, rate limits, cooldown), `computer_vision/monitor.py` (webcam/video command), `backend/app/pose_extractor.py` (MediaPipe wrapper and landmark mapping), `backend/app/vision.py` (features and classifiers), `backend/app/api/events.py` (`/vision/pose` for keypoints sent by another service).

## Run
```
pip install mediapipe opencv-python
python computer_vision/download_pose_model.py                   # one-time, needs internet (pose_landmarker_lite.task)
python computer_vision/monitor.py --elderly-id 1 --source clip.mp4 --dry-run     # prints the events it would send
python computer_vision/monitor.py --elderly-id 1 --source 0 --api http://localhost:8000 --device-key $DEVICE_KEY --show
```
Settings: `--min-conf` (default 0.6, also `FALL_MIN_CONFIDENCE`), `--every` seconds between analysed frames (0.2), `--cooldown` seconds between fall events (30), `POSE_MIN_VISIBILITY` (0.5, frames where the body is not clearly visible are dropped), `POSE_MODEL_PATH`.

## Privacy
Frames live only inside `PoseExtractor.keypoints()`; nothing is written to disk and the pipeline keeps no image (tested). Only an event with a label and a number leaves the machine. `--show` displays the live window locally, off by default.

## What was tested here and what was not
| Part | Status |
|---|---|
| Pipeline logic: fall sent once with cooldown, activity rate-limited, no-person frames, no frame retention | **tested** (`computer_vision/tests`, fake extractor) |
| Reading a real video file with OpenCV (written by the test) | **tested** |
| MediaPipe landmark index mapping and low-visibility rejection | **tested** (fake landmarks) |
| Pose model + rules classification on keypoints | **tested on synthetic keypoints only** (see MODEL_EVALUATION.md) |
| MediaPipe pose estimation on real images/video | **NOT run**: the `.task` model cannot be downloaded offline and there is no camera |
| Webcam capture, `--show`, posting to a live backend | **NOT run** |
| Accuracy on real footage (lighting, occlusion, camera angle) | **unknown**: expect it to be worse than the synthetic numbers |

## Hardware and speed (not measured here; typical guidance, verify on your machine)
MediaPipe Pose Landmarker "lite" runs on a normal laptop CPU at roughly interactive rates; the pipeline analyses 5 frames per second by default, which is plenty for fall detection and keeps CPU low. No GPU is needed. A 720p camera at 1.5-3 m with the whole body visible works best; side views of a person on the floor are the hardest case. YOLO-Pose would need a GPU for comfortable real time and was not used.

## Limits
One person per camera (`num_poses=1`), a fall out of view or behind furniture is invisible, a single-frame lying posture without a preceding drop is classed as lying not falling (by design: avoids false alarms for someone resting on a sofa or floor).
