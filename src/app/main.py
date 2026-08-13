# src/app/main.py - G.R.E.A.T. Application Entry Point
# DEBT-002 behoben: on_event(startup) -> Lifespan Context Manager
# REQ-1202: React-Frontend wird als StaticFiles ausgeliefert (Production Build)
# REQ-4007: GREAT_PORT Umgebungsvariable für portierbare Konfiguration
# REQ-4009: Strukturiertes Logging via structlog
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .config import GREAT_PORT, GREAT_HOST
from .database import Base, engine
from .routers import api_projects, api_generate, api_dataclasses, api_health
from .system_dataclasses import seed_system_dataclasses
from .logging_config import setup_logging, get_logger

FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

# REQ-4009: Logging initialisieren
setup_logging()
log = get_logger("great.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_db()
    # REQ-2005: System-Datenklassen beim ersten Start anlegen
    from .database import SessionLocal
    db = SessionLocal()
    try:
        seed_system_dataclasses(db)
    finally:
        db.close()
    yield


app = FastAPI(title="G.R.E.A.T. API", version="1.0.0", lifespan=lifespan)


# REQ-4009: Request/Response-Logging Middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Strukturiertes Logging für HTTP-Requests und Responses."""
    start = time.time()
    try:
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)
        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration,
        )
        return response
    except Exception as exc:
        duration = round((time.time() - start) * 1000, 2)
        log.error(
            "http_request_failed",
            method=request.method,
            path=request.url.path,
            duration_ms=duration,
            error=str(exc),
        )
        raise


def _migrate_db() -> None:
    if engine.url.get_backend_name() != "sqlite":
        return
    with engine.begin() as conn:
        cols = conn.exec_driver_sql("PRAGMA table_info('values')").fetchall()
        have = {c[1] for c in cols}
        if "allowed" not in have:
            conn.exec_driver_sql("ALTER TABLE 'values' ADD COLUMN allowed INTEGER DEFAULT 1")
            conn.exec_driver_sql("UPDATE 'values' SET allowed=1 WHERE allowed IS NULL")
        if "vtype" not in have:
            conn.exec_driver_sql("ALTER TABLE 'values' ADD COLUMN vtype TEXT DEFAULT 'string'")
            conn.exec_driver_sql("UPDATE 'values' SET vtype='string' WHERE vtype IS NULL")
        cols_rules = conn.exec_driver_sql("PRAGMA table_info('rules')").fetchall()
        rules_have = {c[1] for c in cols_rules}
        if "then_values_json" not in rules_have:
            conn.exec_driver_sql("ALTER TABLE 'rules' ADD COLUMN then_values_json TEXT")
        cols_vals = conn.exec_driver_sql("PRAGMA table_info('values')").fetchall()
        vals_have = {c[1] for c in cols_vals}
        if "order_index" not in vals_have:
            conn.exec_driver_sql("ALTER TABLE 'values' ADD COLUMN order_index INTEGER NOT NULL DEFAULT 0")
        # REQ-2005: is_system Flag fuer Datenklassen
        dc_cols = conn.exec_driver_sql("PRAGMA table_info('dataclasses')").fetchall()
        dc_have = {c[1] for c in dc_cols}
        if "is_system" not in dc_have:
            conn.exec_driver_sql("ALTER TABLE 'dataclasses' ADD COLUMN is_system INTEGER NOT NULL DEFAULT 0")
        # REQ-2004: Editierbarer Name fuer Generierungen
        gen_cols = conn.exec_driver_sql("PRAGMA table_info('generations')").fetchall()
        gen_have = {c[1] for c in gen_cols}
        if "name" not in gen_have:
            conn.exec_driver_sql("ALTER TABLE 'generations' ADD COLUMN name TEXT")
        # REQ-3008: Default-Wert pro Kategorie
        if "is_default" not in have:
            conn.exec_driver_sql("ALTER TABLE 'values' ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0")


# ---------------------------------------------------------------------------
# API-Routers (unveraendert)
# ---------------------------------------------------------------------------

app.include_router(api_projects.router, prefix="/api")
app.include_router(api_generate.router, prefix="/api")
app.include_router(api_dataclasses.router, prefix="/api")
app.include_router(api_health.router, prefix="/api")
# REQ-3011: HTMX-Router archiviert (2026-06-29)

# ---------------------------------------------------------------------------
# React-Frontend (Production Build) - REQ-1202
# ---------------------------------------------------------------------------

if FRONTEND_DIST.exists():
    # Statische Assets (JS, CSS, Icons)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/app", include_in_schema=False)
    @app.get("/app/{path:path}", include_in_schema=False)
    @app.get("/dataclasses", include_in_schema=False)
    def serve_react(path: str = ""):
        return FileResponse(str(FRONTEND_DIST / "index.html"))

# ---------------------------------------------------------------------------
# Komfort-Redirects
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    # Zeige React-App wenn Build vorhanden, sonst HTMX-Fallback
    if FRONTEND_DIST.exists():
        return RedirectResponse(url="/app")
    return RedirectResponse(url="/ui/projects")

@app.get("/ui", include_in_schema=False)
def ui_root():
    return RedirectResponse(url="/app")

@app.get("/whoami", include_in_schema=False)
def whoami():
    return {
        "module": __name__,
        "file": __file__,
        "frontend_dist": str(FRONTEND_DIST),
        "frontend_available": FRONTEND_DIST.exists(),
        "routes": sorted([r.path for r in app.routes])[:20],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=GREAT_HOST, port=GREAT_PORT, reload=True)
