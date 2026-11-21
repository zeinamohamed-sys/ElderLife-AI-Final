"""Runs every test suite of the project and prints one honest table (passed / failed / skipped / not run).   python tests/run_all.py
Frontend tests need node >= 20 and either `npm install` in frontend/ or FRONTEND_NODE_MODULES=<dir with react, react-dom, esbuild>."""
import os, pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).parents[1]; ENV = dict(os.environ, PYTHONWARNINGS="ignore")
def run(cmd, cwd=ROOT, env=ENV):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env); return p.returncode, p.stdout + p.stderr
def unittest_result(name, cmd, cwd=ROOT):
    rc, out = run(cmd, cwd); m = re.search(r"Ran (\d+) tests?", out); s = re.search(r"skipped=(\d+)", out); n = int(m.group(1)) if m else 0; sk = int(s.group(1)) if s else 0
    failed = len(re.findall(r"^(FAIL|ERROR):", out, re.M)); return {"suite": name, "ran": n, "passed": n - failed - sk if m else 0, "failed": failed, "skipped": sk, "ok": rc == 0 and bool(m)}
res = [unittest_result("backend (unit, structure, dashboard, accel, API*)", [sys.executable, "-m", "unittest", "discover", "-s", "tests"], ROOT / "backend"),
       unittest_result("ml (features, SisFall/CASAS/image pipelines on generated files)", [sys.executable, "-m", "unittest", "discover", "-s", "ml/tests", "-t", "."]),
       unittest_result("computer_vision (pipeline with fake extractor + video file)", [sys.executable, "-m", "unittest", "discover", "-s", "computer_vision/tests", "-t", "."]),
       unittest_result("power_bi (assets vs backend exports)", [sys.executable, "-m", "unittest", "power_bi.tests.test_assets"])]
fe = ROOT / "frontend"; extra = os.environ.get("FRONTEND_NODE_MODULES"); has = (fe / "node_modules").exists() or extra
if has:
    rc, out = run(["node", "tests/run.mjs"], fe); t = re.search(r"# tests (\d+)", out); p = re.search(r"# pass (\d+)", out); f = re.search(r"# fail (\d+)", out)
    res.append({"suite": "frontend (render tests, locales, charts)", "ran": int(t.group(1)) if t else 0, "passed": int(p.group(1)) if p else 0, "failed": int(f.group(1)) if f else 0, "skipped": 0, "ok": rc == 0 and bool(t)})
else: res.append({"suite": "frontend (render tests, locales, charts)", "ran": 0, "passed": 0, "failed": 0, "skipped": 0, "ok": None, "note": "NOT RUN: npm install or FRONTEND_NODE_MODULES needed"})
rc, out = run([sys.executable, "tools/check_names.py", "backend", "ml", "computer_vision", "tools", "power_bi", "tests"]); res.append({"suite": "static name check (all Python)", "ran": 1, "passed": int(rc == 0), "failed": int(rc != 0), "skipped": 0, "ok": rc == 0, "note": "" if rc == 0 else out[-300:]})
print(f"{'suite':70s} {'ran':>5} {'pass':>5} {'fail':>5} {'skip':>5}")
for r in res: print(f"{r['suite']:70s} {r['ran']:>5} {r['passed']:>5} {r['failed']:>5} {r['skipped']:>5}  {'OK' if r['ok'] else 'NOT RUN' if r['ok'] is None else 'FAILED'} {r.get('note', '')}")
print("* backend API integration tests need fastapi+httpx installed; without them they are SKIPPED, not passed.")
sys.exit(0 if all(r["ok"] in (True, None) for r in res) else 1)
