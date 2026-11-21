# Dataset registry (verified against the sources on 2026-11-20 unless marked)

## SisFall (accelerometer, falls and ADLs): the first real dataset to use
- **Source:** Sucerquia, López, Vargas-Bonilla, "SisFall: A Fall and Movement Dataset", *Sensors* 17(1):198, 2017, https://doi.org/10.3390/s17010198 (open access article). Dataset page from the paper: http://sistemic.udea.edu.co/investigacion/proyectos/english-falls/?lang=en (SISTEMIC group, Universidad de Antioquia). A community mirror of the files exists on GitHub (`Fall-Prevention-Team/sisfallData`); prefer the official page.
- **License:** the *article* is open access (CC BY). **The license/terms of the data files were not found in the sources I could read: check the download page and the repository before redistributing; do not commit the data.** Cite the paper.
- **Content (from the dataset Readme):** 38 volunteers: SA01-SA23 adults (19-30 y), SE01-SE15 elderly (60-75 y). 19 ADL types (D01-D19) and 15 fall types (F01-F15), 5 trials each (R01-R05), 4510 files. Only SE06 (elderly) simulated falls; the other SE subjects did ADLs only. Waist-worn board, 200 Hz, ADXL345 (+-16 g), ITG3200 gyro, MMA8451Q (+-8 g). Files: `D01_SA01_R01.txt`, 9 comma-separated columns ending with `;`. Conversion for ADXL345: `g = raw * 32 / 2^13`.
- **Our use:** ADXL345 only, decimated to 50 Hz, 3 s windows (`ml/preprocessing/sisfall.py`). Fall windows must contain the impact; ADL windows slide with 1.5 s stride; ambiguous windows of fall recordings are dropped.
- **Limitations:** simulated falls by healthy young volunteers on mats (real falls of frail people differ, the paper itself reports the gap), waist sensor only, only one elderly person fell, ADL recordings are long so windows are heavily imbalanced (this is realistic), windows from one recording overlap (hence subject-wise splits).
- **Download:** `python -m ml.data.download_datasets get sisfall --url <direct zip link you are allowed to use>` or unzip by hand into `ml/data/raw/sisfall/`; check with `python -m ml.data.download_datasets status` (expects 4510 files).

## CASAS smart-home event logs (daily-activity baselines)
- **Source:** CASAS, Washington State University (https://casas.wsu.edu/datasets). Zenodo deposits found: "CASAS Smart Home dataset (aruba, cairo, milan, tulum): free living, motion, door, temperature, activity labels" https://zenodo.org/records/17180309 (about 33 MB, one file per home, columns date, time, sensor id, message) and a larger "raw" deposit https://zenodo.org/records/16343844 (about 1.5 GB). Reference: Cook et al., "CASAS: A Smart Home in a Box", *Computer* 46(7), 2013.
- **License:** **not read from the Zenodo pages; open each record and copy its license here before use.** The team's notebook used files named `atmo*.csv`; **I could not confirm which CASAS release these are**, so record it.
- **Our use:** `ml/preprocessing/casas.py` (hourly motion/door counts per home-day, day-level features), `ml/evaluation/eda_casas.py`, `ml/training/casas_baselines.py`.
- **Limitations:** few homes; household composition differs per dataset (check each description: several residents or pets confound "personal"), no real anomaly labels (hence injected anomalies), sensor layouts differ per home, parsing assumptions: whitespace/comma separated `date time sensor message`.
- **Different people from the other datasets:** never join CASAS with SisFall or the images by person.

## Fall images (team dataset)
- **Source/license: unknown. The notebook shows 374 train + 111 validation images and no corrupt files. Record the source (e.g. Roboflow or Kaggle project URL) and its license here.**
- **Our use:** `ml/preprocessing/fall_images.py` validates, removes duplicates, groups frames by source video, extracts keypoints with MediaPipe, and keeps only keypoint features. `ml/training/train_fall_images.py` trains a posture classifier with group-wise splits.
- **Limitations:** very small, frames from the same video are near-duplicates (group split mandatory), single frames carry no motion, faces are personal data (do not publish images).
