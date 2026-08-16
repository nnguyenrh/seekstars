from datetime import datetime, timezone

from starseek.models.enums import Planet, AspectType
from starseek.models.chart import (
    BirthChart, InterAspect, OverlayPlacement, SynastryReport,
)
from starseek.core.ephemeris import RawPosition
from starseek.core.houses import assign_house
from starseek.core.aspects import (
    ASPECT_ANGLES, MAJOR_ASPECTS, ASPECT_EXCLUDED,
    angular_distance, _get_orb, _is_applying,
)


def _planets_to_raw(chart: BirthChart) -> list[RawPosition]:
    return [
        RawPosition(
            planet=p.planet,
            longitude=p.longitude,
            latitude=p.latitude,
            distance=0.0,
            speed=p.speed,
            is_retrograde=p.is_retrograde,
            sign=p.sign,
            degree_in_sign=p.sign_degree,
        )
        for p in chart.planets
    ]


def find_inter_aspects(
    positions_a: list[RawPosition],
    positions_b: list[RawPosition],
    include_minor: bool = False,
    orbs: dict[AspectType, float] | None = None,
) -> list[InterAspect]:
    aspects_to_check = (
        ASPECT_ANGLES if include_minor
        else {k: v for k, v in ASPECT_ANGLES.items() if k in MAJOR_ASPECTS}
    )

    a_filtered = [p for p in positions_a if p.planet not in ASPECT_EXCLUDED]
    b_filtered = [p for p in positions_b if p.planet not in ASPECT_EXCLUDED]

    results: list[InterAspect] = []
    for pos_a in a_filtered:
        for pos_b in b_filtered:
            dist = angular_distance(pos_a.longitude, pos_b.longitude)

            for aspect_type, angle in aspects_to_check.items():
                orb_limit = _get_orb(aspect_type, pos_a.planet, pos_b.planet, orbs)
                actual_orb = abs(dist - angle)

                if actual_orb <= orb_limit:
                    applying = _is_applying(pos_a, pos_b, angle)
                    results.append(InterAspect(
                        planet_a=pos_a.planet,
                        planet_b=pos_b.planet,
                        aspect_type=aspect_type,
                        exact_angle=round(dist, 4),
                        orb=round(actual_orb, 4),
                        is_applying=applying,
                    ))
                    break

    return results


def compute_overlay(chart_from: BirthChart, chart_into: BirthChart) -> list[OverlayPlacement]:
    placements = []
    for p in chart_from.planets:
        house = assign_house(p.longitude, chart_into.houses)
        placements.append(OverlayPlacement(
            planet=p.planet,
            planet_sign=p.sign,
            planet_degree=round(p.sign_degree, 4),
            overlay_house=house,
        ))
    return placements


def calculate_synastry(
    chart_a: BirthChart,
    chart_b: BirthChart,
    include_minor_aspects: bool = False,
) -> SynastryReport:
    raw_a = _planets_to_raw(chart_a)
    raw_b = _planets_to_raw(chart_b)

    inter_aspects = find_inter_aspects(
        raw_a, raw_b, include_minor=include_minor_aspects
    )

    a_in_b = compute_overlay(chart_a, chart_b)
    b_in_a = compute_overlay(chart_b, chart_a)

    return SynastryReport(
        chart_a=chart_a,
        chart_b=chart_b,
        inter_aspects=inter_aspects,
        a_in_b_houses=a_in_b,
        b_in_a_houses=b_in_a,
        computed_at=datetime.now(timezone.utc),
    )
