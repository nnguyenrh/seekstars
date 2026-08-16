import json
from datetime import datetime, timezone

import pytest

from starseek.models.enums import Planet, Sign, HouseSystem, AspectType
from starseek.models.input import BirthData
from starseek.models.chart import BirthChart, TransitPosition, TransitAspect, TransitReport
from starseek.core.chart import build_chart
from starseek.core.transits import calculate_transits, find_cross_aspects
from starseek.core.ephemeris import (
    init_ephemeris, close_ephemeris, datetime_to_jd, calculate_planet, RawPosition,
)
from starseek.core.aspects import angular_distance
from starseek.formatters.json_fmt import transit_to_json, transit_to_dict
from starseek.formatters.markdown_fmt import transit_to_markdown


@pytest.fixture
def null_island_chart():
    birth_data = BirthData(
        name="Null Island",
        birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        house_system=HouseSystem.PLACIDUS,
    )
    return build_chart(birth_data)


@pytest.fixture
def known_transit_dt():
    return datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


class TestTransitCalculation:
    def test_calculate_transits_returns_report(self, null_island_chart):
        transit_dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        report = calculate_transits(null_island_chart, transit_dt=transit_dt)

        assert isinstance(report, TransitReport)
        assert report.natal_chart_id is None
        assert report.natal_name == "Null Island"
        assert report.transit_datetime == transit_dt

    def test_transit_positions_complete(self, null_island_chart, known_transit_dt):
        report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)

        assert len(report.transit_positions) == 14
        planet_names = {p.planet for p in report.transit_positions}
        assert Planet.SUN in planet_names
        assert Planet.MOON in planet_names
        assert Planet.MERCURY in planet_names
        assert Planet.PLUTO in planet_names
        assert Planet.CHIRON in planet_names
        assert Planet.LILITH in planet_names

    def test_transit_positions_have_valid_data(self, null_island_chart, known_transit_dt):
        report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)

        for pos in report.transit_positions:
            assert 0.0 <= pos.longitude < 360.0
            assert isinstance(pos.sign, Sign)
            assert 0.0 <= pos.sign_degree < 30.0
            assert 0 <= pos.sign_minute < 60

    def test_transit_aspects_found(self, null_island_chart, known_transit_dt):
        report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)

        assert len(report.transit_aspects) > 0
        for aspect in report.transit_aspects:
            assert isinstance(aspect.transit_planet, Planet)
            assert isinstance(aspect.natal_planet, Planet)
            assert isinstance(aspect.aspect_type, AspectType)
            assert aspect.orb >= 0

    def test_default_transit_time_is_now(self, null_island_chart):
        before = datetime.now(timezone.utc)
        report = calculate_transits(null_island_chart)
        after = datetime.now(timezone.utc)

        assert before <= report.transit_datetime <= after

    def test_transit_with_minor_aspects(self, null_island_chart, known_transit_dt):
        major_report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)
        minor_report = calculate_transits(
            null_island_chart, transit_dt=known_transit_dt, include_minor_aspects=True
        )

        assert len(minor_report.transit_aspects) >= len(major_report.transit_aspects)

    def test_transit_sun_position_known_date(self, null_island_chart):
        transit_dt = datetime(2026, 3, 20, 12, 0, 0, tzinfo=timezone.utc)
        report = calculate_transits(null_island_chart, transit_dt=transit_dt)

        sun = next(p for p in report.transit_positions if p.planet == Planet.SUN)
        assert sun.sign in (Sign.PISCES, Sign.ARIES)
        assert 355.0 <= sun.longitude <= 5.0 or 355.0 <= sun.longitude < 360.0 or 0.0 <= sun.longitude <= 5.0


class TestCrossAspects:
    def test_conjunction_detection(self):
        transit_pos = RawPosition(
            planet=Planet.SUN, longitude=100.0, latitude=0.0,
            distance=1.0, speed=1.0, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=10.0,
        )
        natal_pos = RawPosition(
            planet=Planet.MOON, longitude=102.0, latitude=0.0,
            distance=1.0, speed=0.5, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=12.0,
        )

        aspects = find_cross_aspects([transit_pos], [natal_pos])
        assert len(aspects) == 1
        assert aspects[0].aspect_type == AspectType.CONJUNCTION
        assert aspects[0].transit_planet == Planet.SUN
        assert aspects[0].natal_planet == Planet.MOON

    def test_opposition_detection(self):
        transit_pos = RawPosition(
            planet=Planet.MARS, longitude=10.0, latitude=0.0,
            distance=1.5, speed=0.5, is_retrograde=False,
            sign=Sign.ARIES, degree_in_sign=10.0,
        )
        natal_pos = RawPosition(
            planet=Planet.VENUS, longitude=190.0, latitude=0.0,
            distance=0.7, speed=1.2, is_retrograde=False,
            sign=Sign.LIBRA, degree_in_sign=10.0,
        )

        aspects = find_cross_aspects([transit_pos], [natal_pos])
        assert len(aspects) == 1
        assert aspects[0].aspect_type == AspectType.OPPOSITION

    def test_no_aspect_when_out_of_orb(self):
        transit_pos = RawPosition(
            planet=Planet.SATURN, longitude=100.0, latitude=0.0,
            distance=9.5, speed=0.03, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=10.0,
        )
        natal_pos = RawPosition(
            planet=Planet.SATURN, longitude=150.0, latitude=0.0,
            distance=9.5, speed=0.03, is_retrograde=False,
            sign=Sign.VIRGO, degree_in_sign=0.0,
        )

        aspects = find_cross_aspects([transit_pos], [natal_pos])
        assert len(aspects) == 0

    def test_south_node_excluded(self):
        transit_pos = RawPosition(
            planet=Planet.SOUTH_NODE, longitude=100.0, latitude=0.0,
            distance=0.0, speed=-0.05, is_retrograde=True,
            sign=Sign.CANCER, degree_in_sign=10.0,
        )
        natal_pos = RawPosition(
            planet=Planet.SUN, longitude=100.0, latitude=0.0,
            distance=1.0, speed=1.0, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=10.0,
        )

        aspects = find_cross_aspects([transit_pos], [natal_pos])
        assert len(aspects) == 0

    def test_applying_aspect(self):
        transit_pos = RawPosition(
            planet=Planet.MARS, longitude=118.0, latitude=0.0,
            distance=1.5, speed=0.7, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=28.0,
        )
        natal_pos = RawPosition(
            planet=Planet.SUN, longitude=120.0, latitude=0.0,
            distance=1.0, speed=0.0, is_retrograde=False,
            sign=Sign.LEO, degree_in_sign=0.0,
        )

        aspects = find_cross_aspects([transit_pos], [natal_pos])
        assert len(aspects) == 1
        assert aspects[0].is_applying is True


class TestTransitFormatters:
    def test_transit_to_json(self, null_island_chart, known_transit_dt):
        report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)
        json_str = transit_to_json(report)
        parsed = json.loads(json_str)

        assert "transit_datetime" in parsed
        assert "transit_positions" in parsed
        assert "transit_aspects" in parsed
        assert len(parsed["transit_positions"]) == 14

    def test_transit_to_dict(self, null_island_chart, known_transit_dt):
        report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)
        d = transit_to_dict(report)

        assert isinstance(d, dict)
        assert "transit_positions" in d
        assert "transit_aspects" in d

    def test_transit_to_markdown(self, null_island_chart, known_transit_dt):
        report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)
        md = transit_to_markdown(report)

        assert "# Transits for Null Island" in md
        assert "## Current Planetary Positions" in md
        assert "## Transit-to-Natal Aspects" in md
        assert "| Planet | Sign | Degree | Rx |" in md
        assert "Sun" in md

    def test_transit_markdown_without_name(self, null_island_chart, known_transit_dt):
        null_island_chart.name = None
        report = calculate_transits(null_island_chart, transit_dt=known_transit_dt)
        md = transit_to_markdown(report)

        assert "# Transit Report" in md
