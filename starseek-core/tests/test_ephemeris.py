import pytest
from datetime import datetime

from starseek.core.ephemeris import (
    init_ephemeris, close_ephemeris, datetime_to_jd,
    calculate_planet, calculate_houses,
)
from starseek.models.enums import Planet, Sign


@pytest.fixture(autouse=True)
def setup_ephe():
    init_ephemeris()
    yield
    close_ephemeris()


class TestJulianDay:
    def test_y2k_epoch(self):
        dt = datetime(2000, 1, 1, 0, 0, 0)
        jd = datetime_to_jd(dt)
        assert abs(jd - 2451544.5) < 0.001

    def test_timezone_conversion(self):
        dt_utc = datetime(2000, 1, 1, 5, 0, 0)
        jd_utc = datetime_to_jd(dt_utc)

        dt_naive = datetime(2000, 1, 1, 0, 0, 0)
        jd_est = datetime_to_jd(dt_naive, "America/New_York")

        assert abs(jd_utc - jd_est) < 0.001


class TestPlanetPositions:
    def test_sun_y2k(self, reference_charts):
        fixture = reference_charts["null_island"]
        fix_sun = next(p for p in fixture["planets"] if p["name"] == "Sun")

        pos = calculate_planet(
            datetime_to_jd(datetime(2000, 1, 1, 0, 0, 0)),
            Planet.SUN
        )

        assert abs(pos.longitude - fix_sun["longitude"]) < 0.001
        assert pos.sign == Sign.CAPRICORN

    def test_moon_y2k(self, reference_charts):
        fixture = reference_charts["null_island"]
        fix_moon = next(p for p in fixture["planets"] if p["name"] == "Moon")

        pos = calculate_planet(
            datetime_to_jd(datetime(2000, 1, 1, 0, 0, 0)),
            Planet.MOON
        )

        assert abs(pos.longitude - fix_moon["longitude"]) < 0.001

    def test_south_node_opposite_north(self):
        jd = datetime_to_jd(datetime(2000, 1, 1, 0, 0, 0))
        nn = calculate_planet(jd, Planet.NORTH_NODE)
        sn = calculate_planet(jd, Planet.SOUTH_NODE)

        diff = abs(nn.longitude - sn.longitude)
        assert abs(diff - 180.0) < 0.01 or abs(diff - 180.0 + 360) < 0.01

    def test_chiron_position(self, reference_charts):
        fixture = reference_charts["null_island"]
        fix_chiron = next(p for p in fixture["planets"] if p["name"] == "Chiron")

        pos = calculate_planet(
            datetime_to_jd(datetime(2000, 1, 1, 0, 0, 0)),
            Planet.CHIRON
        )

        assert abs(pos.longitude - fix_chiron["longitude"]) < 0.001

    def test_retrograde_detection(self, reference_charts):
        fixture = reference_charts["retrograde_heavy"]
        jd = fixture["julian_day"]

        saturn = calculate_planet(jd, Planet.SATURN)
        neptune = calculate_planet(jd, Planet.NEPTUNE)
        pluto = calculate_planet(jd, Planet.PLUTO)

        assert saturn.is_retrograde
        assert neptune.is_retrograde
        assert pluto.is_retrograde

    def test_venus_station_speed(self, reference_charts):
        fixture = reference_charts["retrograde_heavy"]
        jd = fixture["julian_day"]

        venus = calculate_planet(jd, Planet.VENUS)
        assert abs(venus.speed) < 0.5


class TestHouses:
    def test_house_cusps_count(self):
        jd = datetime_to_jd(datetime(2000, 1, 1, 0, 0, 0))
        cusps = calculate_houses(jd, 0.0, 0.0)
        assert len(cusps.cusps) == 12

    def test_ascendant_matches_fixture(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        cusps = calculate_houses(jd, 0.0, 0.0)
        assert abs(cusps.ascendant - fixture["ascendant"]) < 0.001

    def test_diana_ascendant(self, reference_charts):
        fixture = reference_charts["princess_diana"]
        jd = fixture["julian_day"]
        cusps = calculate_houses(jd, 52.8306, 0.5145)
        asc_sign = Sign(["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"][int(cusps.ascendant / 30)])
        assert asc_sign == Sign.SAGITTARIUS
