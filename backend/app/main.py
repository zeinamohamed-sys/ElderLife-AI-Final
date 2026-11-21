"""Application factory: middleware and routers."""
import json
from app import i18n
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import CORS_ORIGINS
from app.api import alerts, analytics, auth_admin, careplan, demo, elder_self, elderly, events, sensors, dashboard
from app.core.logging_config import setup_logging
from app.services.scheduler import lifespan

setup_logging()
app = FastAPI(title="ElderLife AI API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def language(request: Request, call_next):
    """Remember the requested language on the request and translate API error messages."""
    request.state.lang = i18n.negotiate(request.headers.get("accept-language"))
    resp = await call_next(request)
    if resp.status_code < 400: return resp
    try:
        body = b"".join([chunk async for chunk in resp.body_iterator])
        data = json.loads(body)
    except Exception:
        return resp
    if not isinstance(data, dict) or not isinstance(data.get("detail"), str): return resp
    detail = i18n.translate_error(data["detail"], request.state.lang)
    if detail == data["detail"]: return resp
    data["detail"] = detail
    headers = {k: v for k, v in resp.headers.items() if k.lower() != "content-length"}
    return JSONResponse(data, status_code=resp.status_code, headers=headers)

for _m in (auth_admin, elderly, events, sensors, dashboard, dashboard, careplan, elder_self, alerts, analytics, demo):
    app.include_router(_m.router)

# Backwards compatibility: code and tests that did `from app.main import X` keep working (noqa: reexport)
from app.core.config import *  # noqa: F401,F403
from app.db.database import *  # noqa: F401,F403
from app.db.models import *  # noqa: F401,F403
from app.security import *  # noqa: F401,F403
from app.services.people import *  # noqa: F401,F403
from app.services.risk_service import *  # noqa: F401,F403
from app.services.care import *  # noqa: F401,F403
from app.services.scheduler import tick  # noqa: F401
from app.notifications import *  # noqa: F401,F403
