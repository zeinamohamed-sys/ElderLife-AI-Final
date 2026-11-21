"""Consistency of the Power BI assets with the backend: sample CSV headers == real export headers; every table[column] used in the M and DAX files exists."""
import csv, pathlib, re, unittest
ROOT = pathlib.Path(__file__).parents[2]; PB = ROOT / "power_bi"; TABLES = ["alerts", "risk", "events", "checkins", "careplan", "people"]
def backend_headers():
    src = (ROOT / "backend/app/api/analytics.py").read_text(encoding="utf-8"); out = {}
    for n in TABLES:
        m = re.search(r'name == "%s":\s*(?:#.*)?\n\s*w\.writerow\(\[([^\]]*)\]\)' % n, src); out[n] = [c.strip().strip('"') for c in m.group(1).split(",")]
    return out
def added_columns():
    m_text = (PB / "power_query.m").read_text(encoding="utf-8"); out = {n: set() for n in TABLES}
    for block in re.split(r"// ---------- (\w+)", m_text)[1:]:
        pass
    parts = re.split(r"// ---------- (\w+)[^\n]*\n", m_text); 
    for name, body in zip(parts[1::2], parts[2::2]):
        if name in out: out[name] |= set(re.findall(r'Table\.AddColumn\([^,]+, "(\w+)"', body))
    return out
class PowerBiAssets(unittest.TestCase):
    def test_sample_headers_match_backend_exports(self):
        for n, cols in backend_headers().items():
            with open(PB / "sample_data" / f"sample_{n}.csv", encoding="utf-8") as f: self.assertEqual(next(csv.reader(f)), cols, n)
    def test_sample_data_is_consistent(self):
        rows = {n: list(csv.DictReader(open(PB / "sample_data" / f"sample_{n}.csv", encoding="utf-8"))) for n in TABLES}; ids = {r["elderly_id"] for r in rows["people"]}
        for n in TABLES[:-1]: self.assertTrue({r["elderly_id"] for r in rows[n]} <= ids, n); self.assertGreater(len(rows[n]), 20, n)
        self.assertTrue(all(0 <= float(r["score"]) <= 1 for r in rows["risk"])); self.assertTrue({r["level"] for r in rows["alerts"]} <= {"Normal", "Low", "Medium", "High", "Critical"})
    def test_every_column_used_in_dax_exists(self):
        valid = {n: set(c) | added_columns()[n] for n, c in backend_headers().items()}; dax = (PB / "measures.dax").read_text(encoding="utf-8"); bad = []
        for t, c in re.findall(r"\b(alerts|risk|events|checkins|careplan|people)\[(\w+)\]", dax):
            if c not in valid[t]: bad.append(f"{t}[{c}]")
        self.assertEqual(bad, [])
    def test_dax_measures_referenced_exist(self):
        dax = (PB / "measures.dax").read_text(encoding="utf-8"); defined = set(re.findall(r"^([A-Za-z+ \-%]+?) = ", dax, re.M)); used = set(re.findall(r"\[([A-Za-z+ \-%]+)\]", dax))
        cols = {c for n in TABLES for c in backend_headers()[n]}; missing = {u for u in used if u not in defined and u not in cols and u not in {"Date"}}; self.assertEqual(missing, set(), missing)
    def test_m_script_has_all_tables_and_the_header_the_backend_expects(self):
        m = (PB / "power_query.m").read_text(encoding="utf-8")
        for n in TABLES: self.assertIn(f'fnExport("{n}")', m)
        self.assertIn("X-Export-Key", m); self.assertIn('RelativePath = "export/"', m)
        self.assertIn("X-Export-Key", (ROOT / "backend/app/security.py").read_text(encoding="utf-8").replace("x_export_key", "X-Export-Key"))
if __name__ == "__main__": unittest.main()
