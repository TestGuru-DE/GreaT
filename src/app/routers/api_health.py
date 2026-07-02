"""Health-Check Endpoint – REQ-4008."""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(tags=["health"])
_start_time = time.time()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Systemstatus prüfen: Status, Version, DB-Erreichbarkeit, Uptime."""
    # DB-Ping
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    uptime_seconds = int(time.time() - _start_time)
    status = "ok" if db_status == "ok" else "degraded"

    return {
        "status": status,
        "version": "1.0.0",
        "db": db_status,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
