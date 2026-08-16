import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe

from starseek.models.enums import Planet, Sign, sign_from_longitude, degree_in_sign

_DEFAULT_EPHE_PATH = str(Path(__file__).resolve().parent.parent.parent / "data" / "ephe")


PLANET_TO_SWE: dict[Planet, int | None] = {
    Planet.SUN: swe.SUN,
    Planet.MOON: swe.MOON,
    Planet.MERCURY: swe.MERCURY,
    Planet.VENUS: swe.VENUS,
    Planet.MARS: swe.MARS,
    Planet.JUPITER: swe.JUPITER,
    Planet.SATURN: swe.SATURN,
    Planet.URANUS: swe.URANUS,
    Planet.NEPTUNE: swe.NEPTUNE,
    Planet.PLUTO: swe.PLUTO,
    Planet.NORTH_NODE: swe.TRUE_NODE,
    Planet.SOUTH_NODE: None,
    Planet.CHIRON: swe.CHIRON,
    Planet.LILITH: swe.MEAN_APOG,
}

HOUSE_SYSTEM_BYTES = {
    "Placidus": b"P",
    "Whole Sign": b"W",
}


@dataclass
class RawPosition:
    planet: Planet
    longitude: float
    latitude: float
    distance: float
    speed: float
    is_retrograde: bool
    sign: Sign
    degree_in_sign: float


@dataclass
class HouseCusps:
    cusps: list[float]
    ascendant: float
    midheaven: float


def init_ephemeris(ephe_path: str | None = None) -> None:
    path = ephe_path if ephe_path is not None else _DEFAULT_EPHE_PATH
    swe.set_ephe_path(path)


def close_ephemeris() -> None:
    swe.close()


def datetime_to_jd(dt: datetime, tz_name: str | None = None) -> float:
    if dt.tzinfo is not None:
        dt_utc = dt.astimezone(timezone.utc)
    elif tz_name:
        local_tz = ZoneInfo(tz_name)
        dt_local = dt.replace(tzinfo=local_tz)
        dt_utc = dt_local.astimezone(timezone.utc)
    else:
        dt_utc = dt.replace(tzinfo=timezone.utc)

    hour_decimal = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_decimal)


def calculate_planet(jd: float, planet: Planet) -> RawPosition:
    if planet == Planet.SOUTH_NODE:
        nn = calculate_planet(jd, Planet.NORTH_NODE)
        sn_lon = (nn.longitude + 180.0) % 360.0
        return RawPosition(
            planet=Planet.SOUTH_NODE,
            longitude=sn_lon,
            latitude=0.0,
            distance=nn.distance,
            speed=nn.speed,
            is_retrograde=nn.is_retrograde,
            sign=sign_from_longitude(sn_lon),
            degree_in_sign=degree_in_sign(sn_lon),
        )

    body_id = PLANET_TO_SWE[planet]
    xx, _ = swe.calc_ut(jd, body_id)

    lon = xx[0]
    return RawPosition(
        planet=planet,
        longitude=lon,
        latitude=xx[1],
        distance=xx[2],
        speed=xx[3],
        is_retrograde=xx[3] < 0,
        sign=sign_from_longitude(lon),
        degree_in_sign=degree_in_sign(lon),
    )


def calculate_houses(jd: float, lat: float, lng: float, house_system: str = "Placidus") -> HouseCusps:
    hs_byte = HOUSE_SYSTEM_BYTES.get(house_system, b"P")
    cusps, ascmc = swe.houses(jd, lat, lng, hs_byte)

    cusp_list = list(cusps)

    return HouseCusps(
        cusps=cusp_list,
        ascendant=ascmc[0],
        midheaven=ascmc[1],
    )
