"""Tiny stand-ins for fastapi / sqlalchemy / pydantic so the module wiring can be import-tested where those packages cannot be installed.
They only record routes and accept the calls made at import time; they do NOT run queries or HTTP. Used only when the real packages are missing."""
import sys, types
def install():
    def mod(name, **kw):
        m = types.ModuleType(name); m.__dict__.update(kw); sys.modules[name] = m; return m
    class _Any:
        def __init__(self, *a, **k): pass
        def __call__(self, *a, **k): return _Any()
        def __getattr__(self, n): return _Any()
    class HTTPException(Exception):
        def __init__(self, status_code, detail=None): self.status_code, self.detail = status_code, detail
    class APIRouter:
        def __init__(self): self.routes = []
        def _reg(self, method):
            def deco(path, **kw):
                def wrap(fn): self.routes.append((method, path, fn)); return fn
                return wrap
            return deco
        def __getattr__(self, n):
            if n in ("get", "post", "put", "delete"): return self._reg(n.upper())
            raise AttributeError(n)
    class FastAPI(APIRouter):
        def __init__(self, *a, **k): super().__init__(); self.included = []
        def add_middleware(self, *a, **k): pass
        def middleware(self, kind): return lambda fn: fn
        def include_router(self, r): self.routes.extend(r.routes)
    mod("fastapi", FastAPI=FastAPI, APIRouter=APIRouter, Depends=lambda f=None: f, HTTPException=HTTPException, Header=lambda d=None: d, Request=object)
    mod("fastapi.middleware"); mod("fastapi.middleware.cors", CORSMiddleware=object)
    mod("fastapi.responses", Response=object, JSONResponse=object)
    class BaseModel: pass
    mod("pydantic", BaseModel=BaseModel, Field=lambda *a, **k: None)
    class Base:
        class metadata:
            @staticmethod
            def create_all(engine): pass
    def declarative_base(): return Base
    cols = {n: _Any() for n in ("Column", "Integer", "String", "Float", "DateTime", "ForeignKey", "text")}
    import contextlib
    class _Eng(_Any):
        @contextlib.contextmanager
        def begin(self): yield _Any()
    cols.update(create_engine=lambda *a, **k: _Eng(), inspect=lambda *a, **k: types.SimpleNamespace(get_columns=lambda t: []),
                event=types.SimpleNamespace(listens_for=lambda *a, **k: (lambda fn: fn)))
    cols["Column"] = lambda *a, **k: _Any(); cols["ForeignKey"] = lambda *a, **k: _Any(); cols["text"] = lambda *a, **k: _Any()
    mod("sqlalchemy", **cols); mod("sqlalchemy.orm", declarative_base=declarative_base, sessionmaker=lambda **k: _Any())
