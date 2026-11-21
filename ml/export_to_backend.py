"""Copy a trained fall model into the backend: python ml/export_to_backend.py [ml/models/real_sisfall_fall.joblib]
The backend refuses models whose metadata is not 'real...'. Train and run the backend with the SAME scikit-learn version (pickle compatibility)."""
import pathlib, shutil, sys
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "ml/models/real_sisfall_fall.joblib"); dst = pathlib.Path("backend/app/models/accel_fall.joblib")
if not src.exists(): raise SystemExit(f"{src} not found: train on the real SisFall data first (docs/MODEL_TRAINING.md)")
shutil.copy(src, dst); print("copied", src, "->", dst)
