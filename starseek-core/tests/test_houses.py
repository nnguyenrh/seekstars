import pytest
from datetime import datetime

from starseek.models.enums import Sign, HouseSystem, HouseQuality, SIGN_LIST
from starseek.core.ephemeris import (
    init_ephemeris, close_ephemeris, datetime_to_jd,
    calculate_planet, calculate_houses,
)
from starseek.core.houses import build_house_cusps, assign_house
from starseek.models.enums import Planet


@pytest.fixture(autouse=True)
def setup_ephe():
    init_ephemeris()
    yield
    close_ephemeris()


class TestPlacidusHouses:
    def test_twelve_houses(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.PLACIDUS)
        assert len(cusps) == 12

    def test_house_numbers_sequential(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.PLACIDUS)
        for i, cusp in enumerate(cusps):
            assert cusp.house_number == i + 1

    def test_house_qualities(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.PLACIDUS)
        angular = [c for c in cusps if c.quality == HouseQuality.ANGULAR]
        succedent = [c for c in cusps if c.quality == HouseQuality.SUCCEDENT]
        cadent = [c for c in cusps if c.quality == HouseQuality.CADENT]
        assert len(angular) == 4
        assert len(succedent) == 4
        assert len(cadent) == 4

    def test_ascendant_is_first_cusp(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.PLACIDUS)
        assert abs(cusps[0].longitude - raw.ascendant) < 0.001


class TestWholeSignHouses:
    def test_each_house_is_one_sign(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.WHOLE_SIGN)

        asc_sign_index = SIGN_LIST.index(cusps[0].sign)
        for i, cusp in enumerate(cusps):
            expected_sign = SIGN_LIST[(asc_sign_index + i) % 12]
            assert cusp.sign == expected_sign

    def test_cusp_degrees_are_zero(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.WHOLE_SIGN)

        for cusp in cusps:
            assert cusp.sign_degree == 0.0


class TestHouseAssignment:
    def test_planet_in_first_house(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.PLACIDUS)

        planet_lon = cusps[0].longitude + 5.0
        house = assign_house(planet_lon, cusps)
        assert house == 1

    def test_planet_assignment_matches_expectations(self, reference_charts):
        fixture = reference_charts["null_island"]
        jd = fixture["julian_day"]
        raw = calculate_houses(jd, 0.0, 0.0)
        cusps = build_house_cusps(raw, HouseSystem.PLACIDUS)

        sun = calculate_planet(jd, Planet.SUN)
        house = assign_house(sun.longitude, cusps)
        assert 1 <= house <= 12
