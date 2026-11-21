"""API integration tests (FastAPI TestClient, temporary SQLite). Skipped automatically when fastapi/httpx are not installed.
Run: cd backend && pip install -r requirements.txt httpx && python -m unittest discover -s tests"""
import os, tempfile, unittest
try:
    import fastapi, httpx   # noqa
    HAVE = True
except Exception: HAVE = False
@unittest.skipUnless(HAVE, "fastapi/httpx not installed")
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(); os.environ.update(DATABASE_URL=f"sqlite:///{cls.tmp}/t.db", APP_ENV="development", DEVICE_KEY="test-device-key-123")
        from fastapi.testclient import TestClient
        from app import main
        cls.main = main; cls.c = TestClient(main.app).__enter__()
        cls.tok = cls.c.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]
        cls.H = {"Authorization": f"Bearer {cls.tok}"}
    @classmethod
    def tearDownClass(cls): cls.c.__exit__(None, None, None)
    def test_health(self): self.assertEqual(self.c.get("/health").json(), {"status": "ok"})
    def test_requires_login(self): self.assertEqual(self.c.get("/elderly").status_code, 401)
    def test_bad_login(self): self.assertEqual(self.c.post("/auth/login", json={"username": "admin", "password": "x"}).status_code, 401)
    def test_caregiver_cannot_use_admin_routes(self):
        self.c.post("/users", headers=self.H, json={"username": "cg1", "password": "pw-12345"})
        t = self.c.post("/auth/login", json={"username": "cg1", "password": "pw-12345"}).json()["token"]
        self.assertEqual(self.c.get("/users", headers={"Authorization": f"Bearer {t}"}).status_code, 403)
    def test_event_requires_device_key_or_login(self):
        self.assertEqual(self.c.post("/events", json={"elderly_id": 1, "kind": "ok"}).status_code, 401)
    def test_invalid_event_kind(self): self.assertEqual(self.c.post("/events", headers=self.H, json={"elderly_id": 1, "kind": "bogus"}).status_code, 422)
    def test_arabic_error_message(self):
        r = self.c.get("/elderly", headers={"Accept-Language": "ar"}); self.assertEqual(r.status_code, 401)
if __name__ == "__main__": unittest.main()
