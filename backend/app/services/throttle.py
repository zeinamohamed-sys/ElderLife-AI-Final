"""Login throttle: after MAX_FAILS wrong passwords for a username within WINDOW_S seconds, further attempts are refused (HTTP 429) until the window ends.
In-memory (per process): enough against guessing on one server; use a reverse proxy or Redis-backed limiter for several workers."""
import threading, time as _time
MAX_FAILS, WINDOW_S = 5, 300
class LoginThrottle:
    def __init__(self, max_fails=MAX_FAILS, window_s=WINDOW_S, clock=_time.monotonic):
        self.max, self.window, self.clock, self.fails, self.lock = max_fails, window_s, clock, {}, threading.Lock()
    def _recent(self, key):
        t = self.clock(); xs = [x for x in self.fails.get(key, []) if t - x < self.window]; self.fails[key] = xs; return xs
    def blocked_for(self, key):
        """seconds left until the user may try again (0 = allowed)"""
        with self.lock:
            xs = self._recent(key)
            return max(0, int(self.window - (self.clock() - xs[0])) + 1) if len(xs) >= self.max else 0
    def failed(self, key):
        with self.lock: self._recent(key); self.fails[key].append(self.clock())
    def ok(self, key):
        with self.lock: self.fails.pop(key, None)
throttle = LoginThrottle()
