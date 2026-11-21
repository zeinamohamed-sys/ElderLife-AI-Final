import unittest
from datetime import datetime, timedelta
from app.services.dashboard import build_summary
from app.services.throttle import LoginThrottle
NOW = datetime(2026, 11, 21, 15, 0)
def person(i, level="Normal", baseline=50, cg=None): return {"id": i, "name": f"P{i}", "level": level, "score": 0.1, "baseline": baseline, "caregiver_id": cg}
def alert(i, eid, level="High", status="open", ago_h=1, resolved_by=None, resp_min=None):
    c = NOW - timedelta(hours=ago_h); return {"id": i, "elderly_id": eid, "level": level, "status": status, "created_at": c, "resolved_at": c + timedelta(minutes=resp_min) if resp_min else None, "resolved_by": resolved_by}
def ev(i, eid, kind, val, ago_h): return {"id": i, "elderly_id": eid, "kind": kind, "value": val, "created_at": NOW - timedelta(hours=ago_h)}
def ci(eid, sched_h_ago, answered): s = NOW - timedelta(hours=sched_h_ago); return {"elderly_id": eid, "scheduled_at": s, "responded_at": s + timedelta(minutes=5) if answered else None}
class DashboardTests(unittest.TestCase):
    def test_empty_is_safe_and_all_zero(self):
        s = build_summary([], [], [], [], [], NOW); self.assertEqual(s["totals"], {"people": 0, "caregivers": 0}); self.assertEqual(s["safety"]["status"], "ok")
        self.assertEqual(s["alerts"]["open"], 0); self.assertEqual(len(s["activity_trend"]), 14); self.assertEqual(len(s["alerts"]["per_day"]), 7); self.assertEqual(s["recent_events"], [])
    def test_levels_alerts_and_status(self):
        s = build_summary([person(1), person(2, "High"), person(3, "Critical")], [alert(1, 3, "Critical"), alert(2, 2, "High", "acknowledged")], [], [], [], NOW)
        self.assertEqual(s["safety"]["levels"], {"Normal": 1, "Low": 0, "Medium": 0, "High": 1, "Critical": 1}); self.assertEqual(s["safety"]["status"], "critical")
        self.assertEqual((s["alerts"]["open"], s["alerts"]["acknowledged"], s["alerts"]["high_or_critical_open"]), (1, 1, 1))
        self.assertEqual(build_summary([person(1, "Medium")], [], [], [], [], NOW)["safety"]["status"], "attention")
    def test_checkins_today_split(self):
        s = build_summary([person(1), person(2), person(3)], [], [], [ci(1, 3, True), ci(2, 2, False), ci(3, 0.1, False), ci(1, 30, False)], [], NOW)   # last one is yesterday: not counted
        self.assertEqual(s["checkins_today"], {"due": 3, "answered": 1, "missed": 1, "pending": 1})
        self.assertIn({"elderly_id": 2, "name": "P2", "kind": "missed_checkin", "ratio": None}, s["anomalies"])
    def test_falls_and_recent_events_order(self):
        e = [ev(1, 1, "fall", .9, 2), ev(2, 1, "fall", .8, 50), ev(3, 1, "activity", 40, 1)] + [ev(10 + i, 1, "ok", 0, 100 + i) for i in range(20)]
        s = build_summary([person(1)], [], e, [], [], NOW); self.assertEqual((s["falls"]["today"], s["falls"]["last_7_days"]), (1, 2))
        self.assertEqual([x["id"] for x in s["recent_events"][:3]], [3, 1, 2]); self.assertEqual(len(s["recent_events"]), 10); self.assertEqual(s["recent_events"][0]["name"], "P1")
    def test_activity_trend_and_drop_anomaly(self):
        e = [ev(1, 1, "activity", 10, 1), ev(2, 1, "activity", 20, 2), ev(3, 1, "activity", 80, 30)]
        s = build_summary([person(1, baseline=50), person(2, baseline=50)], [], e, [], [], NOW)
        today = s["activity_trend"][-1]; self.assertEqual((today["mean"], today["n"]), (15.0, 2)); self.assertEqual(s["activity_trend"][-2]["mean"], 80.0); self.assertIsNone(s["activity_trend"][0]["mean"])
        self.assertEqual([(a["kind"], a["ratio"]) for a in s["anomalies"]], [("activity_drop", 0.3)])   # person 2 has no data today: not flagged
    def test_caregiver_activity(self):
        al = [alert(1, 1, status="resolved", resolved_by="caregiver", resp_min=10, ago_h=5), alert(2, 1, status="resolved", resolved_by="person", resp_min=1), alert(3, 2, "High", "open"), alert(4, 3, status="resolved", resolved_by="caregiver", resp_min=4)]
        s = build_summary([person(1, cg=7), person(2, cg=7), person(3, cg=8)], al, [], [], [{"id": 7, "username": "sara"}, {"id": 8, "username": "omar"}], NOW)
        sara, omar = s["caregivers"]; self.assertEqual((sara["people"], sara["open_alerts"], sara["resolved_7d"], sara["avg_response_min"]), (2, 1, 1, 10.0)); self.assertEqual((omar["resolved_7d"], omar["avg_response_min"]), (1, 4.0))
class ThrottleTests(unittest.TestCase):
    def test_blocks_after_max_fails_and_recovers(self):
        t = [0.0]; th = LoginThrottle(3, 60, clock=lambda: t[0])
        for _ in range(2): th.failed("a")
        self.assertEqual(th.blocked_for("a"), 0); th.failed("a"); self.assertGreater(th.blocked_for("a"), 0); self.assertEqual(th.blocked_for("b"), 0)
        t[0] = 61; self.assertEqual(th.blocked_for("a"), 0)
    def test_success_clears_counter(self):
        th = LoginThrottle(2, 60); th.failed("a"); th.ok("a"); th.failed("a"); self.assertEqual(th.blocked_for("a"), 0)
if __name__ == "__main__": unittest.main()

class ExportAuthTests(unittest.TestCase):
    def test_export_key(self):
        import importlib, os, sys
        os.environ["EXPORT_KEY"] = "export-key-1234567"; os.environ["APP_ENV"] = "development"
        from tests.stubs import install
        try: import fastapi  # noqa
        except Exception: install()
        import app.core.config as cfg; importlib.reload(cfg); import app.security as sec; importlib.reload(sec)
        u = sec.export_auth(authorization=None, x_export_key="export-key-1234567", db=None); self.assertEqual((u.role, u.id), ("admin", 0))
        with self.assertRaises(Exception): sec.export_auth(authorization=None, x_export_key="wrong-key-1234567", db=None)   # falls back to normal login, which refuses
        os.environ.pop("EXPORT_KEY"); importlib.reload(cfg); importlib.reload(sec)
        with self.assertRaises(Exception): sec.export_auth(authorization=None, x_export_key="export-key-1234567", db=None)    # disabled when not configured
