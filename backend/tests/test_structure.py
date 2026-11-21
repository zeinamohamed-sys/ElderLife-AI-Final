"""The split of main.py must not lose or add routes, and every module must import. Runs with the real FastAPI when installed,
otherwise with the stubs in tests/stubs (wiring only, no HTTP)."""
import os, unittest
EXPECTED = """GET /model/info
GET /health
POST /auth/login
GET /auth/me
GET /languages
PUT /auth/lang
POST /users
GET /users
GET /admin/people
PUT /elderly/{eid}/assign
GET /elderly
POST /elderly
GET /elderly/{eid}
GET /elderly/{eid}/timeline
POST /elderly/{eid}/checkin
POST /events
POST /vision/pose
GET /sensor/accel/model
GET /dashboard/summary
GET /events
GET /checkins
GET /careplan
POST /sensor/accel
GET /elderly/{eid}/careplan
POST /elderly/{eid}/careplan
POST /careplan/{iid}/done
DELETE /careplan/{iid}
GET /elder/me
POST /elder/checkin
POST /elder/ok
POST /elder/help
POST /elder/done/{iid}
GET /alerts
POST /alerts/{aid}/ack
GET /notifications
GET /analytics
GET /export/{name}
POST /simulate/seed""".split("\n")
try:
    import fastapi, sqlalchemy, pydantic  # noqa
    REAL = True
except Exception:
    REAL = False
class StructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("DATABASE_URL", "sqlite://")
        if not REAL:
            from tests.stubs import install; install()
        from app import main; cls.main = main
    def test_routes_are_preserved(self):
        if REAL: got = {f"{m} {r.path}" for r in self.main.app.routes for m in getattr(r, "methods", set()) if m in ("GET", "POST", "PUT", "DELETE")}
        else: got = {f"{m} {p}" for m, p, _ in self.main.app.routes}
        self.assertEqual(got & set(EXPECTED), set(EXPECTED), set(EXPECTED) - got)
        extra = {g for g in got if g not in EXPECTED and not g.startswith(("GET /docs", "GET /redoc", "GET /openapi"))}
        self.assertEqual(extra, set())
    def test_backwards_compatible_names(self):
        for n in ("app", "SessionLocal", "User", "Elderly", "Event", "evaluate", "tick", "signals", "DEVICE_KEY", "new_user", "notify"):
            self.assertTrue(hasattr(self.main, n), n)
    def test_models_declare_foreign_keys_in_source(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "app", "db", "models.py"), encoding="utf-8").read()
        self.assertGreaterEqual(src.count("ForeignKey("), 8)
if __name__ == "__main__": unittest.main()
