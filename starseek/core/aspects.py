from dataclasses import dataclass

from starseek.models.enums import Planet, AspectType
from starseek.models.chart import Aspect
from starseek.core.ephemeris import RawPosition


ASPECT_ANGLES: dict[AspectType, float] = {
    AspectType.CONJUNCTION: 0.0,
    AspectType.SEMI_SEXTILE: 30.0,
    AspectType.SEMI_SQUARE: 45.0,
    AspectType.SEXTILE: 60.0,
    AspectType.SQUARE: 90.0,
    AspectType.TRINE: 120.0,
    AspectType.SESQUIQUADRATE: 135.0,
    AspectType.QUINCUNX: 150.0,
    AspectType.OPPOSITION: 180.0,
}

DEFAULT_ORBS: dict[AspectType, float] = {
    AspectType.CONJUNCTION: 8.0,
    AspectType.SEXTILE: 6.0,
    AspectType.SQUARE: 7.0,
    AspectType.TRINE: 8.0,
    AspectType.OPPOSITION: 8.0,
    AspectType.SEMI_SEXTILE: 2.0,
    AspectType.SEMI_SQUARE: 2.0,
    AspectType.SESQUIQUADRATE: 2.0,
    AspectType.QUINCUNX: 3.0,
}

LUMINARY_ORB_BONUS = 2.0

MAJOR_ASPECTS = {
    AspectType.CONJUNCTION,
    AspectType.SEXTILE,
    AspectType.SQUARE,
    AspectType.TRINE,
    AspectType.OPPOSITION,
}

LUMINARIES = {Planet.SUN, Planet.MOON}

ASPECT_EXCLUDED = {Planet.SOUTH_NODE}


def angular_distance(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2)
    return min(diff, 360.0 - diff)


def _get_orb(aspect_type: AspectType, planet_a: Planet, planet_b: Planet, orbs: dict[AspectType, float] | None = None) -> float:
    base_orb = (orbs or DEFAULT_ORBS).get(aspect_type, 2.0)
    if planet_a in LUMINARIES or planet_b in LUMINARIES:
        base_orb += LUMINARY_ORB_BONUS
    return base_orb


def _is_applying(pos_a: RawPosition, pos_b: RawPosition, aspect_angle: float) -> bool:
    current_dist = angular_distance(pos_a.longitude, pos_b.longitude)

    faster = pos_a if abs(pos_a.speed) > abs(pos_b.speed) else pos_b
    slower = pos_b if faster is pos_a else pos_a

    future_fast = (faster.longitude + faster.speed) % 360
    future_slow = (slower.longitude + slower.speed) % 360
    future_dist = angular_distance(future_fast, future_slow)

    future_orb = abs(future_dist - aspect_angle)
    current_orb = abs(current_dist - aspect_angle)

    return future_orb < current_orb


def find_aspects(
    positions: list[RawPosition],
    include_minor: bool = False,
    orbs: dict[AspectType, float] | None = None,
) -> list[Aspect]:
    aspects_to_check = ASPECT_ANGLES if include_minor else {k: v for k, v in ASPECT_ANGLES.items() if k in MAJOR_ASPECTS}
    filtered = [p for p in positions if p.planet not in ASPECT_EXCLUDED]

    results: list[Aspect] = []
    for i in range(len(filtered)):
        for j in range(i + 1, len(filtered)):
            pos_a = filtered[i]
            pos_b = filtered[j]
            dist = angular_distance(pos_a.longitude, pos_b.longitude)

            for aspect_type, angle in aspects_to_check.items():
                orb_limit = _get_orb(aspect_type, pos_a.planet, pos_b.planet, orbs)
                actual_orb = abs(dist - angle)

                if actual_orb <= orb_limit:
                    applying = _is_applying(pos_a, pos_b, angle)
                    results.append(Aspect(
                        planet_a=pos_a.planet,
                        planet_b=pos_b.planet,
                        aspect_type=aspect_type,
                        exact_angle=round(dist, 4),
                        orb=round(actual_orb, 4),
                        is_applying=applying,
                    ))
                    break

    return results
