from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from starseek.api.dependencies import get_settings, get_db_path
from starseek.config import Settings
from starseek.models.input import BirthData
from starseek.models.chart import BirthChart, TransitReport
from starseek.core.chart import build_chart
from starseek.core.transits import calculate_transits
from starseek.formatters.markdown_fmt import to_markdown
from starseek.services.storage import (
    save_chart, load_chart, list_charts, delete_chart,
    cache_location, get_cached_location,
)
from starseek.services.geocoding import (
    geocode_city, GeocodingError, CityNotFoundError, GeoNamesNotConfiguredError,
)

router = APIRouter(prefix="/api/v1", tags=["charts"])


class ChartListResponse(BaseModel):
    charts: list[dict]
    total: int


class TransitRequest(BaseModel):
    transit_datetime: Optional[datetime] = Field(
        None,
        description="Date/time for transit calculation (ISO 8601). Defaults to current time.",
    )
    include_minor_aspects: bool = Field(False, description="Include minor aspects")


@router.post("/charts", status_code=201, response_model=BirthChart)
def create_chart(
    birth_data: BirthData,
    settings: Settings = Depends(get_settings),
    db_path: str = Depends(get_db_path),
):
    if birth_data.city and birth_data.latitude is None:
        resolved = _resolve_city(birth_data.city, db_path, settings.geonames_username)
        birth_data = birth_data.model_copy(update={
            "latitude": resolved.latitude,
            "longitude": resolved.longitude,
            "timezone": resolved.timezone,
            "city": resolved.city_name,
        })

    chart = build_chart(birth_data, ephe_path=settings.ephe_path)
    chart_id = save_chart(db_path, chart)
    chart.id = chart_id
    return chart


@router.get("/charts", response_model=ChartListResponse)
def get_charts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    name: Optional[str] = Query(None),
    db_path: str = Depends(get_db_path),
):
    items, total = list_charts(db_path, limit=limit, offset=offset, name_filter=name)
    charts = [
        {
            "id": item.id,
            "name": item.name,
            "birth_datetime": item.birth_datetime,
            "birth_location": item.birth_location,
            "house_system": item.house_system,
            "created_at": item.created_at,
        }
        for item in items
    ]
    return ChartListResponse(charts=charts, total=total)


@router.get("/charts/{chart_id}", response_model=BirthChart)
def get_chart(chart_id: int, db_path: str = Depends(get_db_path)):
    chart = load_chart(db_path, chart_id)
    if chart is None:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id} not found")
    return chart


@router.delete("/charts/{chart_id}", status_code=204)
def remove_chart(chart_id: int, db_path: str = Depends(get_db_path)):
    deleted = delete_chart(db_path, chart_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id} not found")
    return Response(status_code=204)


@router.get("/charts/{chart_id}/markdown")
def get_chart_markdown(chart_id: int, db_path: str = Depends(get_db_path)):
    chart = load_chart(db_path, chart_id)
    if chart is None:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id} not found")
    md = to_markdown(chart)
    return Response(content=md, media_type="text/markdown")


@router.post("/charts/{chart_id}/transits", response_model=TransitReport)
def get_transits(
    chart_id: int,
    body: TransitRequest = TransitRequest(),
    settings: Settings = Depends(get_settings),
    db_path: str = Depends(get_db_path),
):
    chart = load_chart(db_path, chart_id)
    if chart is None:
        raise HTTPException(status_code=404, detail=f"Chart {chart_id} not found")

    report = calculate_transits(
        chart,
        transit_dt=body.transit_datetime,
        include_minor_aspects=body.include_minor_aspects,
        ephe_path=settings.ephe_path,
    )
    return report


def _resolve_city(city: str, db_path: str, username: str):
    cached = get_cached_location(db_path, city)
    if cached is not None:
        return cached

    if not username:
        raise HTTPException(
            status_code=400,
            detail="GeoNames username not configured and city not in cache. "
                   "Use latitude/longitude/timezone instead.",
        )

    try:
        result = geocode_city(city, username)
    except CityNotFoundError:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    except GeoNamesNotConfiguredError:
        raise HTTPException(status_code=400, detail="GeoNames username not configured")
    except GeocodingError as e:
        raise HTTPException(status_code=502, detail=f"Geocoding service error: {e}")

    cache_location(db_path, city, result)
    return result
