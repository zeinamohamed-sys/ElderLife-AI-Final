"""Logging: one named logger ("elderlife") writing to stderr. LOG_LEVEL=DEBUG|INFO|WARNING (default INFO). Passwords, tokens and codes are never logged."""
import logging, os
log = logging.getLogger("elderlife")
def setup_logging():
    if log.handlers: return
    h = logging.StreamHandler(); h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    log.addHandler(h); log.setLevel(os.getenv("LOG_LEVEL", "INFO").upper()); log.propagate = False
