import pytest

from starseek.models.enums import Planet, Sign, Dignity
from starseek.core.dignities import get_dignity


class TestDignities:
    def test_sun_in_leo_domicile(self):
        assert get_dignity(Planet.SUN, Sign.LEO) == Dignity.DOMICILE

    def test_sun_in_aquarius_detriment(self):
        assert get_dignity(Planet.SUN, Sign.AQUARIUS) == Dignity.DETRIMENT

    def test_sun_in_aries_exaltation(self):
        assert get_dignity(Planet.SUN, Sign.ARIES) == Dignity.EXALTATION

    def test_sun_in_libra_fall(self):
        assert get_dignity(Planet.SUN, Sign.LIBRA) == Dignity.FALL

    def test_sun_in_cancer_peregrine(self):
        assert get_dignity(Planet.SUN, Sign.CANCER) == Dignity.PEREGRINE

    def test_moon_in_cancer_domicile(self):
        assert get_dignity(Planet.MOON, Sign.CANCER) == Dignity.DOMICILE

    def test_moon_in_capricorn_detriment(self):
        assert get_dignity(Planet.MOON, Sign.CAPRICORN) == Dignity.DETRIMENT

    def test_moon_in_taurus_exaltation(self):
        assert get_dignity(Planet.MOON, Sign.TAURUS) == Dignity.EXALTATION

    def test_moon_in_scorpio_fall(self):
        assert get_dignity(Planet.MOON, Sign.SCORPIO) == Dignity.FALL

    def test_moon_in_aquarius_peregrine(self):
        assert get_dignity(Planet.MOON, Sign.AQUARIUS) == Dignity.PEREGRINE

    def test_mercury_domicile_gemini(self):
        assert get_dignity(Planet.MERCURY, Sign.GEMINI) == Dignity.DOMICILE

    def test_mercury_domicile_virgo(self):
        assert get_dignity(Planet.MERCURY, Sign.VIRGO) == Dignity.DOMICILE

    def test_venus_in_pisces_exaltation(self):
        assert get_dignity(Planet.VENUS, Sign.PISCES) == Dignity.EXALTATION

    def test_mars_in_capricorn_exaltation(self):
        assert get_dignity(Planet.MARS, Sign.CAPRICORN) == Dignity.EXALTATION

    def test_jupiter_in_cancer_exaltation(self):
        assert get_dignity(Planet.JUPITER, Sign.CANCER) == Dignity.EXALTATION

    def test_saturn_in_libra_exaltation(self):
        assert get_dignity(Planet.SATURN, Sign.LIBRA) == Dignity.EXALTATION

    def test_north_node_peregrine(self):
        assert get_dignity(Planet.NORTH_NODE, Sign.ARIES) == Dignity.PEREGRINE

    def test_south_node_peregrine(self):
        assert get_dignity(Planet.SOUTH_NODE, Sign.LEO) == Dignity.PEREGRINE
