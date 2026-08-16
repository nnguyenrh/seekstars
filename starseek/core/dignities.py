from starseek.models.enums import Planet, Sign, Dignity

DIGNITY_TABLE: dict[Planet, dict[Dignity, list[Sign]]] = {
    Planet.SUN: {
        Dignity.DOMICILE: [Sign.LEO],
        Dignity.DETRIMENT: [Sign.AQUARIUS],
        Dignity.EXALTATION: [Sign.ARIES],
        Dignity.FALL: [Sign.LIBRA],
    },
    Planet.MOON: {
        Dignity.DOMICILE: [Sign.CANCER],
        Dignity.DETRIMENT: [Sign.CAPRICORN],
        Dignity.EXALTATION: [Sign.TAURUS],
        Dignity.FALL: [Sign.SCORPIO],
    },
    Planet.MERCURY: {
        Dignity.DOMICILE: [Sign.GEMINI, Sign.VIRGO],
        Dignity.DETRIMENT: [Sign.SAGITTARIUS, Sign.PISCES],
        Dignity.EXALTATION: [Sign.VIRGO],
        Dignity.FALL: [Sign.PISCES],
    },
    Planet.VENUS: {
        Dignity.DOMICILE: [Sign.TAURUS, Sign.LIBRA],
        Dignity.DETRIMENT: [Sign.SCORPIO, Sign.ARIES],
        Dignity.EXALTATION: [Sign.PISCES],
        Dignity.FALL: [Sign.VIRGO],
    },
    Planet.MARS: {
        Dignity.DOMICILE: [Sign.ARIES, Sign.SCORPIO],
        Dignity.DETRIMENT: [Sign.LIBRA, Sign.TAURUS],
        Dignity.EXALTATION: [Sign.CAPRICORN],
        Dignity.FALL: [Sign.CANCER],
    },
    Planet.JUPITER: {
        Dignity.DOMICILE: [Sign.SAGITTARIUS, Sign.PISCES],
        Dignity.DETRIMENT: [Sign.GEMINI, Sign.VIRGO],
        Dignity.EXALTATION: [Sign.CANCER],
        Dignity.FALL: [Sign.CAPRICORN],
    },
    Planet.SATURN: {
        Dignity.DOMICILE: [Sign.CAPRICORN, Sign.AQUARIUS],
        Dignity.DETRIMENT: [Sign.CANCER, Sign.LEO],
        Dignity.EXALTATION: [Sign.LIBRA],
        Dignity.FALL: [Sign.ARIES],
    },
    Planet.URANUS: {
        Dignity.DOMICILE: [Sign.AQUARIUS],
        Dignity.DETRIMENT: [Sign.LEO],
        Dignity.EXALTATION: [Sign.SCORPIO],
        Dignity.FALL: [Sign.TAURUS],
    },
    Planet.NEPTUNE: {
        Dignity.DOMICILE: [Sign.PISCES],
        Dignity.DETRIMENT: [Sign.VIRGO],
        Dignity.EXALTATION: [Sign.LEO],
        Dignity.FALL: [Sign.AQUARIUS],
    },
    Planet.PLUTO: {
        Dignity.DOMICILE: [Sign.SCORPIO],
        Dignity.DETRIMENT: [Sign.TAURUS],
        Dignity.EXALTATION: [Sign.ARIES],
        Dignity.FALL: [Sign.LIBRA],
    },
}


def get_dignity(planet: Planet, sign: Sign) -> Dignity:
    planet_dignities = DIGNITY_TABLE.get(planet)
    if planet_dignities is None:
        return Dignity.PEREGRINE

    for dignity, signs in planet_dignities.items():
        if sign in signs:
            return dignity

    return Dignity.PEREGRINE
