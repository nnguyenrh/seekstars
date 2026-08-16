from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from starseek.api.dependencies import get_settings, get_db_path
from starseek.config import Settings
from starseek.services.geocoding import (
    search_city, GeocodingResult,
    GeocodingError, CityNotFoundError, GeoNamesNotConfiguredError,
)

router = APIRouter(prefix="/api/v1", tags=["geocoding"])


class GeocodeRequest(BaseModel):
    city: str = Field(..., min_length=1, description="City name to look up")


class GeocodeResultItem(BaseModel):
    city_name: str
    country: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str


class GeocodeResponse(BaseModel):
    results: list[GeocodeResultItem]


@router.post("/geocode", response_model=GeocodeResponse)
def geocode(
    request: GeocodeRequest,
    settings: Settings = Depends(get_settings),
):
    if not settings.geonames_username:
        raise HTTPException(
            status_code=400,
            detail="GeoNames username not configured. Set GEONAMES_USERNAME in .env.",
        )

    try:
        results = search_city(request.city, settings.geonames_username)
    except CityNotFoundError:
        raise HTTPException(status_code=404, detail=f"No results found for '{request.city}'")
    except GeocodingError as e:
        raise HTTPException(status_code=502, detail=f"Geocoding service error: {e}")

    items = [
        GeocodeResultItem(
            city_name=r.city_name,
            country=r.country,
            country_code=r.country_code,
            latitude=r.latitude,
            longitude=r.longitude,
            timezone=r.timezone,
        )
        for r in results
    ]

    return GeocodeResponse(results=items)
