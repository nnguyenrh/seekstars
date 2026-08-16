from datetime import datetime, timezone

import swisseph as swe

from starseek.models.enums import Planet, HouseSystem
from starseek.models.input import BirthData
from starseek.models.chart import BirthChart
from starseek.core.ephemeris import (
    init_ephemeris, close_ephemeris, datetime_to_jd, calculate_planet,
)
from starseek.core.chart import build_chart


def _jd_to_datetime(jd: float) -> datetime:
    year, month, day, hour_frac = swe.revjul(jd)
    hour = int(hour_frac)
    minute_frac = (hour_frac - hour) * 60
    minute = int(minute_frac)
    second = int((minute_frac - minute) * 60)
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


def find_solar_return(
    natal_sun_longitude: float,
    year: int,
    ephe_path: str | None = None,
) -> datetime:
    init_ephemeris(ephe_path)
    try:
        start_jd = swe.julday(year, 1, 1, 0.0)
        jd_cross = swe.solcross_ut(natal_sun_longitude, start_jd)
        return _jd_to_datetime(jd_cross)
    finally:
        close_ephemeris()


def find_lunar_return(
    natal_moon_longitude: float,
    after_dt: datetime | None = None,
    ephe_path: str | None = None,
) -> datetime:
    init_ephemeris(ephe_path)
    try:
        if after_dt is None:
            after_dt = datetime.now(timezone.utc)
        start_jd = datetime_to_jd(after_dt)
        jd_cross = swe.mooncross_ut(natal_moon_longitude, start_jd)
        return _jd_to_datetime(jd_cross)
    finally:
        close_ephemeris()


def calculate_return(
    natal_chart: BirthChart,
    return_type: str = "solar",
    year: int | None = None,
    location_lat: float | None = None,
    location_lng: float | None = None,
    location_tz: str | None = None,
    location_city: str | None = None,
    house_system: HouseSystem | None = None,
    ephe_path: str | None = None,
) -> BirthChart:
    natal_sun = next(p for p in natal_chart.planets if p.planet == Planet.SUN)
    natal_moon = next(p for p in natal_chart.planets if p.planet == Planet.MOON)

    if return_type == "solar":
        if year is None:
            year = datetime.now(timezone.utc).year
        return_dt = find_solar_return(natal_sun.longitude, year, ephe_path)
    else:
        return_dt = find_lunar_return(natal_moon.longitude, ephe_path=ephe_path)

    lat = location_lat if location_lat is not None else natal_chart.latitude
    lng = location_lng if location_lng is not None else natal_chart.longitude
    tz = location_tz if location_tz is not None else natal_chart.timezone
    hs = house_system if house_system is not None else natal_chart.house_system

    return_type_label = "Solar" if return_type == "solar" else "Lunar"
    if return_type == "solar":
        name = f"{return_type_label} Return {year}"
    else:
        name = f"{return_type_label} Return"
    if natal_chart.name:
        name = f"{natal_chart.name} - {name}"

    birth_data = BirthData(
        name=name,
        birth_datetime=return_dt,
        city=location_city,
        latitude=lat,
        longitude=lng,
        timezone=tz,
        house_system=hs,
    )

    return build_chart(birth_data, ephe_path=ephe_path)
