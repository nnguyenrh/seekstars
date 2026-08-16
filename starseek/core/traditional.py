from starseek.models.enums import Planet, Sign, Dignity
from starseek.models.chart import PlanetPosition, Aspect, BirthChart
from starseek.core.dignities import DIGNITY_TABLE, get_dignity


SIGN_RULERS: dict[Sign, Planet] = {
    Sign.ARIES: Planet.MARS,
    Sign.TAURUS: Planet.VENUS,
    Sign.GEMINI: Planet.MERCURY,
    Sign.CANCER: Planet.MOON,
    Sign.LEO: Planet.SUN,
    Sign.VIRGO: Planet.MERCURY,
    Sign.LIBRA: Planet.VENUS,
    Sign.SCORPIO: Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN: Planet.SATURN,
    Sign.AQUARIUS: Planet.SATURN,
    Sign.PISCES: Planet.JUPITER,
}

DIURNAL_BENEFIC = Planet.JUPITER
NOCTURNAL_BENEFIC = Planet.VENUS
DIURNAL_MALEFIC = Planet.SATURN
NOCTURNAL_MALEFIC = Planet.MARS

DIURNAL_PLANETS = {Planet.SUN, Planet.JUPITER, Planet.SATURN}
NOCTURNAL_PLANETS = {Planet.MOON, Planet.VENUS, Planet.MARS}
NEUTRAL_PLANETS = {Planet.MERCURY}

SECT_RELEVANT = (
    DIURNAL_PLANETS | NOCTURNAL_PLANETS | NEUTRAL_PLANETS
)


def determine_sect(sun_longitude: float, asc_longitude: float) -> str:
    diff = (sun_longitude - asc_longitude) % 360
    if diff < 180:
        return "diurnal"
    return "nocturnal"


def get_sect_status(planet: Planet, sect: str) -> str:
    if planet in NEUTRAL_PLANETS:
        return "neutral"
    if planet not in SECT_RELEVANT:
        return "neutral"
    if sect == "diurnal":
        return "in_sect" if planet in DIURNAL_PLANETS else "out_of_sect"
    else:
        return "in_sect" if planet in NOCTURNAL_PLANETS else "out_of_sect"


def build_domicile_lord_chain(
    planet: Planet,
    planet_signs: dict[Planet, Sign],
) -> list[str]:
    if planet not in planet_signs:
        return [planet.value]

    chain: list[str] = [planet.value]
    visited: set[Planet] = {planet}
    current = planet

    while True:
        sign = planet_signs.get(current)
        if sign is None:
            break
        ruler = SIGN_RULERS.get(sign)
        if ruler is None:
            break

        if ruler in visited:
            chain.append(ruler.value)
            break

        chain.append(ruler.value)
        if ruler == current:
            break

        visited.add(ruler)
        current = ruler

    return chain


def get_all_lord_chains(
    planets: list[PlanetPosition],
) -> list[dict]:
    planet_signs = {p.planet: p.sign for p in planets}
    chains = []
    for p in planets:
        if p.planet in {Planet.NORTH_NODE, Planet.SOUTH_NODE, Planet.CHIRON, Planet.LILITH}:
            continue
        chain = build_domicile_lord_chain(p.planet, planet_signs)
        final = None
        if len(chain) >= 2 and chain[-1] == chain[-2]:
            final = chain[-1]
        chains.append({
            "planet": p.planet.value,
            "chain": chain,
            "final_dispositor": final,
        })
    return chains


def _is_in_good_condition(planet: Planet, planets: list[PlanetPosition], sect: str) -> bool:
    p = next((pp for pp in planets if pp.planet == planet), None)
    if p is None:
        return False
    if p.dignity in (Dignity.DOMICILE, Dignity.EXALTATION):
        return True
    if get_sect_status(planet, sect) == "in_sect":
        return True
    return False


def _is_in_poor_condition(planet: Planet, planets: list[PlanetPosition], sect: str) -> bool:
    p = next((pp for pp in planets if pp.planet == planet), None)
    if p is None:
        return False
    if p.dignity in (Dignity.DETRIMENT, Dignity.FALL):
        return True
    if get_sect_status(planet, sect) == "out_of_sect":
        return True
    return False


def evaluate_bonification(
    planets: list[PlanetPosition],
    aspects: list[Aspect],
    sect: str,
) -> dict[str, list[str]]:
    sect_benefic = DIURNAL_BENEFIC if sect == "diurnal" else NOCTURNAL_BENEFIC
    sect_malefic = DIURNAL_MALEFIC if sect == "diurnal" else NOCTURNAL_MALEFIC

    conditions: dict[str, list[str]] = {}

    for planet_pos in planets:
        planet = planet_pos.planet
        notes: list[str] = []

        for aspect in aspects:
            other = None
            if aspect.planet_a == planet:
                other = aspect.planet_b
            elif aspect.planet_b == planet:
                other = aspect.planet_a

            if other is None:
                continue

            if other == sect_benefic and _is_in_good_condition(sect_benefic, planets, sect):
                notes.append(f"Bonified by {sect_benefic.value} ({aspect.aspect_type.value})")

            if other == sect_malefic and _is_in_poor_condition(sect_malefic, planets, sect):
                notes.append(f"Maltreated by {sect_malefic.value} ({aspect.aspect_type.value})")

        if notes:
            conditions[planet.value] = notes

    return conditions
