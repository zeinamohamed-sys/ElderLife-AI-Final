# Datasets

Full registry with sources, license status, content and limitations: **`ml/data/DATASETS_REGISTRY.md`**. Summary of the current state:

| Dataset | Source known | License verified | Downloaded here | Loader / preprocessing | EDA script | Training script | Run on real data |
|---|---|---|---|---|---|---|---|
| SisFall accelerometer | yes (doi:10.3390/s17010198) | article CC BY; **data terms to confirm** | no (no internet in the sandbox) | `ml/preprocessing/sisfall.py` | `ml/evaluation/eda_sisfall.py` | `ml/training/train_sisfall.py` | **no** |
| CASAS | partly (casas.wsu.edu, Zenodo records); team's `atmo*.csv` release unconfirmed | **no** | no | `ml/preprocessing/casas.py` | `ml/evaluation/eda_casas.py` | `ml/training/casas_baselines.py` | **no** |
| Fall images | **no** (team to fill) | **no** | no | `ml/preprocessing/fall_images.py` | (counts printed by the script) | `ml/training/train_fall_images.py` | **no** |

All loaders were tested on files **generated in the real formats** (`ml/tests/`), which proves the code, not any accuracy. The three datasets describe different people and are never joined per person.

## Getting the data (what you must do)
1. Read the license/terms on each source page and write them into the registry.
2. `python -m ml.data.download_datasets status`; place or download files as the registry describes.
3. Run the pipelines in the order in `docs/MODEL_TRAINING.md`.
