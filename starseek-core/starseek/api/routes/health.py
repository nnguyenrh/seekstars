import sqlite3

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from starseek.api.dependencies import get_settings, get_db_path
from starseek.config import Settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    ephemeris_initialized: bool
    database_connected: bool


@router.get("/api/v1/health", response_model=HealthResponse)
def health_check(
    settings: Settings = Depends(get_settings),
    db_path: str = Depends(get_db_path),
):
    ephe_ok = True
    try:
        import swisseph as swe
        swe.set_ephe_path(settings.ephe_path)
        jd = swe.julday(2000, 1, 1, 0.0)
        swe.calc_ut(jd, swe.SUN)
        swe.close()
    except Exception:
        ephe_ok = False

    db_ok = True
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_ok = False

    status = "healthy" if ephe_ok and db_ok else "degraded"

    return HealthResponse(
        status=status,
        ephemeris_initialized=ephe_ok,
        database_connected=db_ok,
    )
