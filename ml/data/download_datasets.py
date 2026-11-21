"""Dataset registry + helper. Nothing is downloaded unless you pass an explicit --url; `status` shows what is present.
  python -m ml.data.download_datasets status
  python -m ml.data.download_datasets get sisfall --url <direct link to the dataset zip you are allowed to use>
Sources and terms are in ml/data/DATASETS_REGISTRY.md. Always read the dataset's own terms before downloading."""
import argparse, hashlib, pathlib, urllib.request, zipfile
RAW = pathlib.Path(__file__).parent / "raw"
REGISTRY = {
    "sisfall": {"dir": "sisfall", "check": lambda d: len(list(d.rglob("[DF][0-9][0-9]_S[AE][0-9][0-9]_R[0-9][0-9].txt"))), "expected": 4510,
                "page": "http://sistemic.udea.edu.co/investigacion/proyectos/english-falls/?lang=en", "paper": "https://doi.org/10.3390/s17010198"},
    "casas": {"dir": "casas", "check": lambda d: len([p for p in d.rglob("*") if p.is_file()]), "expected": None,
              "page": "https://zenodo.org/records/17180309", "paper": "https://doi.org/10.1109/MC.2012.328"},
    "fall_images": {"dir": "fall_images", "check": lambda d: len(list(d.rglob("*.jpg")) + list(d.rglob("*.png")) + list(d.rglob("*.jpeg"))), "expected": None,
                    "page": "(your team's dataset: record its source here)", "paper": ""},
}
def status():
    for k, v in REGISTRY.items():
        d = RAW / v["dir"]; n = v["check"](d) if d.exists() else 0
        print(f"{k:12s} files found: {n:7d}" + (f" / expected {v['expected']}" if v["expected"] else "") + f"   source: {v['page']}")
def get(name, url, md5=None):
    d = RAW / REGISTRY[name]["dir"]; d.mkdir(parents=True, exist_ok=True); tmp = d / "_download.bin"
    print("downloading", url); urllib.request.urlretrieve(url, tmp)
    if md5 and hashlib.md5(tmp.read_bytes()).hexdigest() != md5: raise SystemExit("MD5 mismatch, file discarded") if tmp.unlink() is None else None
    if zipfile.is_zipfile(tmp):
        with zipfile.ZipFile(tmp) as z:
            for m in z.namelist():  # refuse path traversal
                if m.startswith(("/", "..")) or ".." in pathlib.PurePosixPath(m).parts: raise SystemExit("unsafe path in zip: " + m)
            z.extractall(d)
        tmp.unlink()
    else: tmp.rename(d / pathlib.Path(url).name)
    status()
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd"); sp.add_parser("status"); g = sp.add_parser("get"); g.add_argument("name", choices=REGISTRY); g.add_argument("--url", required=True); g.add_argument("--md5")
    a = ap.parse_args(); status() if a.cmd in (None, "status") else get(a.name, a.url, a.md5)
