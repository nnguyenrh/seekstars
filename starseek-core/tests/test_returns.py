import json
from datetime import datetime, timezone

import pytest

from starseek.models.enums import Planet, Sign, HouseSystem
from starseek.models.input import BirthData
from starseek.models.chart import BirthChart
from starseek.core.chart import build_chart
from starseek.core.returns import (
    find_solar_return, find_lunar_return, calculate_return,
)


@pytest.fixture
def natal_chart():
    bd = BirthData(
        name="Test Person",
        birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        house_system=HouseSystem.PLACIDUS,
    )
    return build_chart(bd)


class TestFindSolarReturn:
    def test_solar_return_found(self, natal_chart):
        natal_sun = next(p for p in natal_chart.planets if p.planet == Planet.SUN)
        return_dt = find_solar_return(natal_sun.longitude, 2026)

        assert return_dt.year == 2026
        assert isinstance(return_dt, datetime)

    def test_solar_return_near_birthday(self, natal_chart):
        natal_sun = next(p for p in natal_chart.planets if p.planet == Planet.SUN)
        return_dt = find_solar_return(natal_sun.longitude, 2026)

        assert return_dt.month == 12 or return_dt.month == 1
        assert abs(return_dt.day - 1) <= 2 or return_dt.day >= 29

    def test_solar_return_different_years(self, natal_chart):
        natal_sun = next(p for p in natal_chart.planets if p.planet == Planet.SUN)
        return_2025 = find_solar_return(natal_sun.longitude, 2025)
        return_2026 = find_solar_return(natal_sun.longitude, 2026)

        assert return_2025.year in (2025, 2026)
        assert return_2026.year in (2026, 2027)
        assert return_2025 != return_2026


class TestFindLunarReturn:
    def test_lunar_return_found(self, natal_chart):
        natal_moon = next(p for p in natal_chart.planets if p.planet == Planet.MOON)
        return_dt = find_lunar_return(natal_moon.longitude)

        assert isinstance(return_dt, datetime)
        assert return_dt >= datetime.now(timezone.utc)

    def test_lunar_return_within_month(self, natal_chart):
        natal_moon = next(p for p in natal_chart.planets if p.planet == Planet.MOON)
        after = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        return_dt = find_lunar_return(natal_moon.longitude, after_dt=after)

        diff = (return_dt - after).days
        assert diff <= 30


class TestCalculateReturn:
    def test_solar_return_chart(self, natal_chart):
        result = calculate_return(natal_chart, return_type="solar", year=2026)

        assert isinstance(result, BirthChart)
        assert len(result.planets) == 14
        assert len(result.houses) == 12
        assert "Solar Return 2026" in result.name

    def test_solar_return_has_natal_name(self, natal_chart):
        result = calculate_return(natal_chart, return_type="solar", year=2026)
        assert "Test Person" in result.name

    def test_lunar_return_chart(self, natal_chart):
        result = calculate_return(natal_chart, return_type="lunar")

        assert isinstance(result, BirthChart)
        assert len(result.planets) == 14
        assert "Lunar Return" in result.name

    def test_return_uses_birth_location_by_default(self, natal_chart):
        result = calculate_return(natal_chart, return_type="solar", year=2026)

        assert result.latitude == natal_chart.latitude
        assert result.longitude == natal_chart.longitude

    def test_return_with_custom_location(self, natal_chart):
        result = calculate_return(
            natal_chart,
            return_type="solar",
            year=2026,
            location_lat=51.5074,
            location_lng=-0.1278,
            location_tz="Europe/London",
        )

        assert result.latitude == pytest.approx(51.5074)
        assert result.longitude == pytest.approx(-0.1278)

    def test_return_default_year_is_current(self, natal_chart):
        result = calculate_return(natal_chart, return_type="solar")
        current_year = datetime.now().year
        assert str(current_year) in result.name

    def test_return_preserves_house_system(self, natal_chart):
        result = calculate_return(natal_chart, return_type="solar", year=2026)
        assert result.house_system == natal_chart.house_system

    def test_return_with_house_system_override(self, natal_chart):
        result = calculate_return(
            natal_chart,
            return_type="solar",
            year=2026,
            house_system=HouseSystem.WHOLE_SIGN,
        )
        assert result.house_system == HouseSystem.WHOLE_SIGN

    def test_solar_return_sun_position_matches_natal(self, natal_chart):
        natal_sun = next(p for p in natal_chart.planets if p.planet == Planet.SUN)
        result = calculate_return(natal_chart, return_type="solar", year=2026)
        return_sun = next(p for p in result.planets if p.planet == Planet.SUN)

        assert abs(return_sun.longitude - natal_sun.longitude) < 0.01

    def test_unnamed_natal_chart(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 6, 15, 12, 0, 0),
            latitude=40.7128, longitude=-74.006, timezone="America/New_York",
        )
        natal = build_chart(bd)
        result = calculate_return(natal, return_type="solar", year=2026)
        assert "Solar Return 2026" in result.name
        assert "None" not in result.name
