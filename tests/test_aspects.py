import pytest

from starseek.core.aspects import angular_distance, find_aspects, MAJOR_ASPECTS
from starseek.core.ephemeris import RawPosition, calculate_planet, datetime_to_jd, init_ephemeris, close_ephemeris
from starseek.models.enums import Planet, Sign, AspectType

from datetime import datetime


@pytest.fixture(autouse=True)
def setup_ephe():
    init_ephemeris()
    yield
    close_ephemeris()


class TestAngularDistance:
    def test_same_point(self):
        assert angular_distance(0.0, 0.0) == 0.0

    def test_opposition(self):
        assert angular_distance(0.0, 180.0) == 180.0

    def test_wraparound(self):
        assert abs(angular_distance(350.0, 10.0) - 20.0) < 0.001

    def test_symmetric(self):
        assert angular_distance(30.0, 120.0) == angular_distance(120.0, 30.0)

    def test_square(self):
        assert abs(angular_distance(0.0, 90.0) - 90.0) < 0.001

    def test_trine(self):
        assert abs(angular_distance(0.0, 120.0) - 120.0) < 0.001


class TestFindAspects:
    def test_diana_sun_mercury_conjunction(self, reference_charts):
        fixture = reference_charts["princess_diana"]
        jd = fixture["julian_day"]

        positions = []
        for planet in [Planet.SUN, Planet.MERCURY]:
            positions.append(calculate_planet(jd, planet))

        aspects = find_aspects(positions)
        assert len(aspects) == 1
        assert aspects[0].aspect_type == AspectType.CONJUNCTION
        assert aspects[0].orb < 8.0

    def test_null_island_aspects_found(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]

        planets = [Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
                   Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO]
        positions = [calculate_planet(jd, p) for p in planets]

        aspects = find_aspects(positions)
        assert len(aspects) > 0

    def test_aspect_orbs_within_limits(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]

        planets = [Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS]
        positions = [calculate_planet(jd, p) for p in planets]

        aspects = find_aspects(positions)
        for a in aspects:
            assert a.orb <= 10.0

    def test_south_node_excluded(self):
        jd = datetime_to_jd(datetime(2000, 1, 1, 0, 0, 0))
        positions = [
            calculate_planet(jd, Planet.SUN),
            calculate_planet(jd, Planet.SOUTH_NODE),
        ]
        aspects = find_aspects(positions)
        for a in aspects:
            assert a.planet_a != Planet.SOUTH_NODE
            assert a.planet_b != Planet.SOUTH_NODE
