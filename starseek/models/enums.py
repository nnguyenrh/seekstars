from enum import Enum


class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MERCURY = "Mercury"
    VENUS = "Venus"
    MARS = "Mars"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    URANUS = "Uranus"
    NEPTUNE = "Neptune"
    PLUTO = "Pluto"
    NORTH_NODE = "North Node"
    SOUTH_NODE = "South Node"
    CHIRON = "Chiron"
    LILITH = "Black Moon Lilith"


class Sign(str, Enum):
    ARIES = "Aries"
    TAURUS = "Taurus"
    GEMINI = "Gemini"
    CANCER = "Cancer"
    LEO = "Leo"
    VIRGO = "Virgo"
    LIBRA = "Libra"
    SCORPIO = "Scorpio"
    SAGITTARIUS = "Sagittarius"
    CAPRICORN = "Capricorn"
    AQUARIUS = "Aquarius"
    PISCES = "Pisces"


SIGN_LIST = list(Sign)

SIGN_ELEMENT: dict[Sign, "Element"] = {}
SIGN_MODALITY: dict[Sign, "Modality"] = {}


class HouseSystem(str, Enum):
    PLACIDUS = "Placidus"
    WHOLE_SIGN = "Whole Sign"


class AspectType(str, Enum):
    CONJUNCTION = "Conjunction"
    SEXTILE = "Sextile"
    SQUARE = "Square"
    TRINE = "Trine"
    OPPOSITION = "Opposition"
    SEMI_SEXTILE = "Semi-sextile"
    SEMI_SQUARE = "Semi-square"
    SESQUIQUADRATE = "Sesquiquadrate"
    QUINCUNX = "Quincunx"


class Dignity(str, Enum):
    DOMICILE = "Domicile"
    DETRIMENT = "Detriment"
    EXALTATION = "Exaltation"
    FALL = "Fall"
    PEREGRINE = "Peregrine"


class HouseQuality(str, Enum):
    ANGULAR = "Angular"
    SUCCEDENT = "Succedent"
    CADENT = "Cadent"


class Element(str, Enum):
    FIRE = "Fire"
    EARTH = "Earth"
    AIR = "Air"
    WATER = "Water"


class Modality(str, Enum):
    CARDINAL = "Cardinal"
    FIXED = "Fixed"
    MUTABLE = "Mutable"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


_ELEMENT_MAP = {
    Sign.ARIES: Element.FIRE, Sign.LEO: Element.FIRE, Sign.SAGITTARIUS: Element.FIRE,
    Sign.TAURUS: Element.EARTH, Sign.VIRGO: Element.EARTH, Sign.CAPRICORN: Element.EARTH,
    Sign.GEMINI: Element.AIR, Sign.LIBRA: Element.AIR, Sign.AQUARIUS: Element.AIR,
    Sign.CANCER: Element.WATER, Sign.SCORPIO: Element.WATER, Sign.PISCES: Element.WATER,
}

_MODALITY_MAP = {
    Sign.ARIES: Modality.CARDINAL, Sign.CANCER: Modality.CARDINAL,
    Sign.LIBRA: Modality.CARDINAL, Sign.CAPRICORN: Modality.CARDINAL,
    Sign.TAURUS: Modality.FIXED, Sign.LEO: Modality.FIXED,
    Sign.SCORPIO: Modality.FIXED, Sign.AQUARIUS: Modality.FIXED,
    Sign.GEMINI: Modality.MUTABLE, Sign.VIRGO: Modality.MUTABLE,
    Sign.SAGITTARIUS: Modality.MUTABLE, Sign.PISCES: Modality.MUTABLE,
}

SIGN_ELEMENT.update(_ELEMENT_MAP)
SIGN_MODALITY.update(_MODALITY_MAP)


def sign_from_longitude(longitude: float) -> Sign:
    return SIGN_LIST[int(longitude / 30) % 12]


def degree_in_sign(longitude: float) -> float:
    return longitude % 30


HOUSE_QUALITY_MAP: dict[int, HouseQuality] = {
    1: HouseQuality.ANGULAR, 2: HouseQuality.SUCCEDENT, 3: HouseQuality.CADENT,
    4: HouseQuality.ANGULAR, 5: HouseQuality.SUCCEDENT, 6: HouseQuality.CADENT,
    7: HouseQuality.ANGULAR, 8: HouseQuality.SUCCEDENT, 9: HouseQuality.CADENT,
    10: HouseQuality.ANGULAR, 11: HouseQuality.SUCCEDENT, 12: HouseQuality.CADENT,
}
