from starseek.models.enums import (
    Sign, HouseSystem, HouseQuality, SIGN_LIST, HOUSE_QUALITY_MAP,
    sign_from_longitude, degree_in_sign,
)
from starseek.models.chart import HouseCusp
from starseek.core.ephemeris import HouseCusps


def build_house_cusps(
    raw_cusps: HouseCusps,
    house_system: HouseSystem,
) -> list[HouseCusp]:
    if house_system == HouseSystem.WHOLE_SIGN:
        return _build_whole_sign_cusps(raw_cusps.ascendant)
    return _build_placidus_cusps(raw_cusps)


def _build_placidus_cusps(raw_cusps: HouseCusps) -> list[HouseCusp]:
    result = []
    for i, lon in enumerate(raw_cusps.cusps):
        house_num = i + 1
        sign = sign_from_longitude(lon)
        result.append(HouseCusp(
            house_number=house_num,
            longitude=round(lon, 6),
            sign=sign,
            sign_degree=round(degree_in_sign(lon), 4),
            quality=HOUSE_QUALITY_MAP[house_num],
        ))
    return result


def _build_whole_sign_cusps(ascendant: float) -> list[HouseCusp]:
    asc_sign_index = int(ascendant / 30) % 12
    result = []
    for i in range(12):
        house_num = i + 1
        sign_index = (asc_sign_index + i) % 12
        sign = SIGN_LIST[sign_index]
        lon = float(sign_index * 30)
        result.append(HouseCusp(
            house_number=house_num,
            longitude=lon,
            sign=sign,
            sign_degree=0.0,
            quality=HOUSE_QUALITY_MAP[house_num],
        ))
    return result


def assign_house(planet_longitude: float, house_cusps: list[HouseCusp]) -> int:
    for i in range(12):
        cusp_lon = house_cusps[i].longitude
        next_cusp_lon = house_cusps[(i + 1) % 12].longitude

        if next_cusp_lon > cusp_lon:
            if cusp_lon <= planet_longitude < next_cusp_lon:
                return house_cusps[i].house_number
        else:
            if planet_longitude >= cusp_lon or planet_longitude < next_cusp_lon:
                return house_cusps[i].house_number

    return 1
