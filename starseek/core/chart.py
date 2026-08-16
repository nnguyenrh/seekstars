from collections import Counter
from datetime import datetime, timezone

from starseek.models.enums import (
    Planet, Sign, HouseSystem, Element, Modality,
    SIGN_ELEMENT, SIGN_MODALITY, sign_from_longitude, degree_in_sign,
)
from starseek.models.chart import (
    BirthChart, PlanetPosition, ChartSummary, Aspect,
)
from starseek.models.input import BirthData
from starseek.core.ephemeris import (
    init_ephemeris, close_ephemeris, datetime_to_jd,
    calculate_planet, calculate_houses, RawPosition,
)
from starseek.core.houses import build_house_cusps, assign_house
from starseek.core.aspects import find_aspects
from starseek.core.dignities import get_dignity


CALCULATED_PLANETS = [
    Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
    Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
    Planet.NORTH_NODE, Planet.SOUTH_NODE, Planet.CHIRON, Planet.LILITH,
]

SUMMARY_PLANETS = {
    Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
    Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
}


def build_chart(
    birth_data: BirthData,
    include_minor_aspects: bool = False,
    ephe_path: str | None = None,
) -> BirthChart:
    init_ephemeris(ephe_path)

    try:
        lat = birth_data.latitude
        lng = birth_data.longitude
        tz_name = birth_data.timezone

        jd = datetime_to_jd(birth_data.birth_datetime, tz_name)

        raw_positions: list[RawPosition] = []
        for planet in CALCULATED_PLANETS:
            pos = calculate_planet(jd, planet)
            raw_positions.append(pos)

        raw_cusps = calculate_houses(jd, lat, lng, birth_data.house_system.value)
        house_cusps = build_house_cusps(raw_cusps, birth_data.house_system)

        planet_positions: list[PlanetPosition] = []
        for pos in raw_positions:
            house_num = assign_house(pos.longitude, house_cusps)
            dignity = get_dignity(pos.planet, pos.sign)
            deg = pos.degree_in_sign
            planet_positions.append(PlanetPosition(
                planet=pos.planet,
                longitude=round(pos.longitude, 6),
                latitude=round(pos.latitude, 6),
                speed=round(pos.speed, 6),
                is_retrograde=pos.is_retrograde,
                sign=pos.sign,
                sign_degree=round(deg, 4),
                sign_minute=int((deg % 1) * 60),
                house=house_num,
                dignity=dignity,
            ))

        aspects = find_aspects(raw_positions, include_minor=include_minor_aspects)

        summary = _build_summary(planet_positions)

        location_str = birth_data.city or f"{lat:.4f}, {lng:.4f}"

        return BirthChart(
            name=birth_data.name,
            birth_datetime=birth_data.birth_datetime,
            birth_location=location_str,
            latitude=lat,
            longitude=lng,
            timezone=tz_name or "UTC",
            house_system=birth_data.house_system,
            planets=planet_positions,
            houses=house_cusps,
            aspects=aspects,
            summary=summary,
            computed_at=datetime.now(timezone.utc),
        )
    finally:
        close_ephemeris()


def _build_summary(planets: list[PlanetPosition]) -> ChartSummary:
    relevant = [p for p in planets if p.planet in SUMMARY_PLANETS]

    element_counts: Counter[Element] = Counter()
    modality_counts: Counter[Modality] = Counter()
    sign_planets: dict[Sign, list[str]] = {}

    for p in relevant:
        element_counts[SIGN_ELEMENT[p.sign]] += 1
        modality_counts[SIGN_MODALITY[p.sign]] += 1
        sign_planets.setdefault(p.sign, []).append(p.planet.value)

    for elem in Element:
        element_counts.setdefault(elem, 0)
    for mod in Modality:
        modality_counts.setdefault(mod, 0)

    dominant_element = max(element_counts, key=lambda e: element_counts[e])
    dominant_modality = max(modality_counts, key=lambda m: modality_counts[m])

    stelliums = []
    for sign, planet_names in sign_planets.items():
        if len(planet_names) >= 3:
            stelliums.append({"sign": sign.value, "planets": planet_names})

    return ChartSummary(
        dominant_element=dominant_element,
        element_counts=dict(element_counts),
        dominant_modality=dominant_modality,
        modality_counts=dict(modality_counts),
        stelliums=stelliums,
    )
