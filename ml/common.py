"""Shared paths, seed and the SYNTHETIC data generators. Everything generated here is synthetic and is labelled as such in every report."""
import pathlib, numpy as np
ROOT = pathlib.Path(__file__).parent
DATA, PROC, MODELS, REPORTS = ROOT / "data", ROOT / "data" / "processed", ROOT / "models", ROOT / "reports"
SEED = 42
FS, WIN_S = 50, 3          # sampling rate (Hz) and window length (s)
ACTIVITIES = ["walking", "standing", "sitting", "stairs", "sit_down_hard", "jumping", "fall"]

def _adl(kind, rng, n, amp):
    t = np.arange(n) / FS; g = np.zeros((n, 3)); g[:, 2] = 1.0
    if kind == "walking":  f = rng.uniform(1.4, 2.2); g[:, 2] += amp * 0.35 * np.sin(2 * np.pi * f * t); g[:, 0] += amp * 0.2 * np.sin(2 * np.pi * f * t + 1)
    elif kind == "stairs": f = rng.uniform(1.0, 1.7); g[:, 2] += amp * 0.55 * np.sin(2 * np.pi * f * t); g[:, 1] += amp * 0.3 * np.sin(2 * np.pi * f * t + .5)
    elif kind == "sitting": g[:, 1] += 0.7; g[:, 2] -= 0.3
    elif kind == "sit_down_hard":  # confusable with a fall: a real impact, but the person stays active afterwards
        i = rng.integers(n // 4, n // 2); g[i:i + 3, 2] += rng.uniform(0.8, 2.6) * amp; g[i + 3:] = _unit(rng) * np.array([0.5, 1.0, 0.8]) + np.array([0, 0.3, 0])
        if rng.random() < 0.6: g[i + 3:] += rng.normal(0, 0.12, (n - i - 3, 3))
    elif kind == "jumping":
        for _ in range(rng.integers(2, 5)): j = rng.integers(0, n - 8); g[j:j + 6, 2] += rng.uniform(1.0, 2.5) * amp; g[j + 6:j + 8, 2] -= 0.5
    return g

def _unit(rng):
    v = rng.normal(0, 1, 3); return v / np.linalg.norm(v) * rng.uniform(0.92, 1.05)

def _fall(rng, n, amp):
    """Falls overlap with ADLs on purpose: 30% have no clear free-fall (slips), impacts can be soft, the final posture is random, 35% keep moving."""
    g = np.zeros((n, 3)); g[:, 2] = 1.0
    i = rng.integers(n // 5, n // 2)
    if rng.random() > 0.3: g[i:i + rng.integers(3, 7), :] *= rng.uniform(0.15, 0.75)
    g[i + 6:i + 9, 2] += rng.uniform(0.5, 3.0) * amp; g[i + 6:i + 9, 0] += rng.uniform(0.1, 1.5)
    g[i + 9:] = _unit(rng)
    if rng.random() < 0.35: g[i + 9:] += rng.normal(0, rng.uniform(0.05, 0.25), (n - i - 9, 3))
    return g

def synth_accel(n_subjects=30, per_subject=40, seed=SEED):
    """Returns (windows[n, T, 3], labels[n] str, subject[n]). Subjects differ in amplitude and noise, so a subject-wise split is meaningful."""
    rng = np.random.default_rng(seed); n = FS * WIN_S; W, y, s = [], [], []
    for sub in range(n_subjects):
        amp, noise = rng.uniform(0.6, 1.5), rng.uniform(0.02, 0.12)
        for _ in range(per_subject):
            kind = "fall" if rng.random() < 0.22 else str(rng.choice(["walking", "standing", "sitting", "stairs", "sit_down_hard", "jumping"], p=[.28, .2, .2, .12, .1, .1]))
            g = _fall(rng, n, amp) if kind == "fall" else _adl(kind, rng, n, amp)
            W.append(g + rng.normal(0, noise, g.shape)); y.append(kind); s.append(sub)
    return np.array(W), np.array(y), np.array(s)

def synth_daily_activity(n_people=40, days=90, seed=SEED):
    """Daily activity totals per person: personal level, weekday pattern, injected abnormal days (abnormal=1)."""
    import pandas as pd
    rng = np.random.default_rng(seed); rows = []
    for p in range(n_people):
        level, spread = rng.uniform(25, 80), rng.uniform(0.08, 0.22)
        for d in range(days):
            wk = 1 + 0.08 * np.sin(2 * np.pi * (d % 7) / 7); bad = rng.random() < 0.05
            v = level * wk * (rng.uniform(0.2, 0.55) if bad else rng.normal(1, spread))
            rows.append((p, d, max(v, 0), int(bad)))
    return pd.DataFrame(rows, columns=["person", "day", "activity", "abnormal"])
