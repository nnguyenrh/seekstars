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
from starseek.core.returns import calculate_return
from starseek.formatters.markdown_fmt import to_markdown
from starseek.services.storage import (
    save_chart, load_chart, list_charts, delete_chart,
    resolve_chart, chart_name_exists,
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


class ReturnRequest(BaseModel):
    return_type: str = Field("solar", description="'solar' or 'lunar'")
    year: Optional[int] = Field(None, description="Year for solar return (default: current year)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Location latitude for return chart")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Location longitude for return chart")
    timezone: Optional[str] = Field(None, description="IANA timezone for return chart location")
    city: Optional[str] = Field(None, description="City for return chart location (triggers geocoding)")
    house_system: Optional[str] = Field(None, description="House system override")
    save: bool = Field(False, description="Save the return chart to database")


@router.post("/charts", status_code=201, response_model=BirthChart)
def create_chart(
    birth_data: BirthData,
    overwrite: bool = Query(False, description="Overwrite existing chart with same name"),
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

    if birth_data.name and not overwrite:
        existing_id = chart_name_exists(db_path, birth_data.name)
        if existing_id is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Chart '{birth_data.name}' already exists (ID {existing_id}). "
                       "Use overwrite=true to replace it.",
            )

    chart = build_chart(birth_data, ephe_path=settings.ephe_path)
    chart_id = save_chart(db_path, chart, overwrite=overwrite)
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


def _resolve_chart_ref(db_path: str, chart_ref: str) -> BirthChart:
    chart = resolve_chart(db_path, chart_ref)
    if chart is None:
        raise HTTPException(status_code=404, detail=f"Chart '{chart_ref}' not found")
    return chart


@router.get("/charts/{chart_ref}", response_model=BirthChart)
def get_chart(chart_ref: str, db_path: str = Depends(get_db_path)):
    return _resolve_chart_ref(db_path, chart_ref)


@router.delete("/charts/{chart_ref}", status_code=204)
def remove_chart(chart_ref: str, db_path: str = Depends(get_db_path)):
    chart = _resolve_chart_ref(db_path, chart_ref)
    deleted = delete_chart(db_path, chart.id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Chart '{chart_ref}' not found")
    return Response(status_code=204)


@router.get("/charts/{chart_ref}/markdown")
def get_chart_markdown(chart_ref: str, db_path: str = Depends(get_db_path)):
    chart = _resolve_chart_ref(db_path, chart_ref)
    md = to_markdown(chart)
    return Response(content=md, media_type="text/markdown")


@router.post("/charts/{chart_ref}/transits", response_model=TransitReport)
def get_transits(
    chart_ref: str,
    body: TransitRequest = TransitRequest(),
    settings: Settings = Depends(get_settings),
    db_path: str = Depends(get_db_path),
):
    chart = _resolve_chart_ref(db_path, chart_ref)

    report = calculate_transits(
        chart,
        transit_dt=body.transit_datetime,
        include_minor_aspects=body.include_minor_aspects,
        ephe_path=settings.ephe_path,
    )
    return report


@router.post("/charts/{chart_ref}/return", response_model=BirthChart)
def get_return(
    chart_ref: str,
    body: ReturnRequest = ReturnRequest(),
    settings: Settings = Depends(get_settings),
    db_path: str = Depends(get_db_path),
):
    chart = _resolve_chart_ref(db_path, chart_ref)

    loc_lat, loc_lng, loc_tz, loc_city = None, None, None, None
    if body.city:
        resolved = _resolve_city(body.city, db_path, settings.geonames_username)
        loc_lat = resolved.latitude
        loc_lng = resolved.longitude
        loc_tz = resolved.timezone
        loc_city = resolved.city_name
    elif body.latitude is not None:
        loc_lat = body.latitude
        loc_lng = body.longitude
        loc_tz = body.timezone

    hs = None
    if body.house_system:
        from starseek.models.enums import HouseSystem
        try:
            hs = HouseSystem(body.house_system)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid house system: {body.house_system}")

    result = calculate_return(
        chart,
        return_type=body.return_type,
        year=body.year,
        location_lat=loc_lat,
        location_lng=loc_lng,
        location_tz=loc_tz,
        location_city=loc_city,
        house_system=hs,
        ephe_path=settings.ephe_path,
    )

    if body.save:
        chart_id = save_chart(db_path, result, overwrite=True)
        result.id = chart_id

    return result


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
