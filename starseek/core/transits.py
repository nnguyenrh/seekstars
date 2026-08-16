from datetime import datetime, timezone

from starseek.models.enums import Planet, sign_from_longitude, degree_in_sign
from starseek.models.chart import (
    BirthChart, TransitPosition, TransitAspect, TransitReport,
)
from starseek.core.ephemeris import (
    init_ephemeris, close_ephemeris, datetime_to_jd,
    calculate_planet, RawPosition,
)
from starseek.core.houses import assign_house
from starseek.core.aspects import (
    ASPECT_ANGLES, MAJOR_ASPECTS, ASPECT_EXCLUDED,
    angular_distance, _get_orb, _is_applying,
)
from starseek.models.enums import AspectType


TRANSIT_PLANETS = [
    Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
    Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
    Planet.NORTH_NODE, Planet.SOUTH_NODE, Planet.CHIRON, Planet.LILITH,
]


def find_cross_aspects(
    transit_positions: list[RawPosition],
    natal_positions: list[RawPosition],
    include_minor: bool = False,
    orbs: dict[AspectType, float] | None = None,
) -> list[TransitAspect]:
    aspects_to_check = (
        ASPECT_ANGLES if include_minor
        else {k: v for k, v in ASPECT_ANGLES.items() if k in MAJOR_ASPECTS}
    )

    t_filtered = [p for p in transit_positions if p.planet not in ASPECT_EXCLUDED]
    n_filtered = [p for p in natal_positions if p.planet not in ASPECT_EXCLUDED]

    results: list[TransitAspect] = []
    for t_pos in t_filtered:
        for n_pos in n_filtered:
            dist = angular_distance(t_pos.longitude, n_pos.longitude)

            for aspect_type, angle in aspects_to_check.items():
                orb_limit = _get_orb(aspect_type, t_pos.planet, n_pos.planet, orbs)
                actual_orb = abs(dist - angle)

                if actual_orb <= orb_limit:
                    applying = _is_applying(t_pos, n_pos, angle)
                    results.append(TransitAspect(
                        transit_planet=t_pos.planet,
                        natal_planet=n_pos.planet,
                        aspect_type=aspect_type,
                        exact_angle=round(dist, 4),
                        orb=round(actual_orb, 4),
                        is_applying=applying,
                    ))
                    break

    return results


def calculate_transits(
    natal_chart: BirthChart,
    transit_dt: datetime | None = None,
    include_minor_aspects: bool = False,
    ephe_path: str | None = None,
) -> TransitReport:
    if transit_dt is None:
        transit_dt = datetime.now(timezone.utc)

    init_ephemeris(ephe_path)

    try:
        jd = datetime_to_jd(transit_dt)

        transit_raw: list[RawPosition] = []
        for planet in TRANSIT_PLANETS:
            pos = calculate_planet(jd, planet)
            transit_raw.append(pos)

        natal_raw: list[RawPosition] = []
        for p in natal_chart.planets:
            natal_raw.append(RawPosition(
                planet=p.planet,
                longitude=p.longitude,
                latitude=p.latitude,
                distance=0.0,
                speed=p.speed,
                is_retrograde=p.is_retrograde,
                sign=p.sign,
                degree_in_sign=p.sign_degree,
            ))

        transit_aspects = find_cross_aspects(
            transit_raw, natal_raw, include_minor=include_minor_aspects
        )

        transit_positions = []
        for pos in transit_raw:
            deg = pos.degree_in_sign
            natal_house = assign_house(pos.longitude, natal_chart.houses)
            transit_positions.append(TransitPosition(
                planet=pos.planet,
                longitude=round(pos.longitude, 6),
                latitude=round(pos.latitude, 6),
                speed=round(pos.speed, 6),
                is_retrograde=pos.is_retrograde,
                sign=pos.sign,
                sign_degree=round(deg, 4),
                sign_minute=int((deg % 1) * 60),
                natal_house=natal_house,
            ))

        return TransitReport(
            natal_chart_id=natal_chart.id,
            natal_name=natal_chart.name,
            natal_sect=natal_chart.sect,
            transit_datetime=transit_dt,
            transit_positions=transit_positions,
            transit_aspects=transit_aspects,
            computed_at=datetime.now(timezone.utc),
        )
    finally:
        close_ephemeris()
