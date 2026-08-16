import json
from datetime import datetime, timezone

import pytest

from starseek.models.enums import Planet, Sign, HouseSystem, AspectType
from starseek.models.input import BirthData
from starseek.models.chart import (
    BirthChart, InterAspect, OverlayPlacement, SynastryReport,
)
from starseek.core.chart import build_chart
from starseek.core.synastry import (
    calculate_synastry, find_inter_aspects, compute_overlay, _planets_to_raw,
)
from starseek.core.ephemeris import RawPosition
from starseek.formatters.json_fmt import synastry_to_json, synastry_to_dict
from starseek.formatters.markdown_fmt import synastry_to_markdown


@pytest.fixture
def chart_a():
    bd = BirthData(
        name="Person A",
        birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        house_system=HouseSystem.PLACIDUS,
    )
    return build_chart(bd)


@pytest.fixture
def chart_b():
    bd = BirthData(
        name="Person B",
        birth_datetime=datetime(1995, 6, 15, 14, 30, 0),
        latitude=51.5074,
        longitude=-0.1278,
        timezone="Europe/London",
        house_system=HouseSystem.PLACIDUS,
    )
    return build_chart(bd)


class TestSynastryCalculation:
    def test_returns_synastry_report(self, chart_a, chart_b):
        report = calculate_synastry(chart_a, chart_b)

        assert isinstance(report, SynastryReport)
        assert report.chart_a.name == "Person A"
        assert report.chart_b.name == "Person B"

    def test_inter_aspects_found(self, chart_a, chart_b):
        report = calculate_synastry(chart_a, chart_b)

        assert len(report.inter_aspects) > 0
        for aspect in report.inter_aspects:
            assert isinstance(aspect, InterAspect)
            assert isinstance(aspect.planet_a, Planet)
            assert isinstance(aspect.planet_b, Planet)
            assert isinstance(aspect.aspect_type, AspectType)
            assert aspect.orb >= 0

    def test_overlay_placements_complete(self, chart_a, chart_b):
        report = calculate_synastry(chart_a, chart_b)

        assert len(report.a_in_b_houses) == 14
        assert len(report.b_in_a_houses) == 14

        for p in report.a_in_b_houses:
            assert isinstance(p, OverlayPlacement)
            assert 1 <= p.overlay_house <= 12
            assert isinstance(p.planet_sign, Sign)

        for p in report.b_in_a_houses:
            assert 1 <= p.overlay_house <= 12

    def test_overlay_asymmetric(self, chart_a, chart_b):
        report = calculate_synastry(chart_a, chart_b)

        a_houses = [p.overlay_house for p in report.a_in_b_houses]
        b_houses = [p.overlay_house for p in report.b_in_a_houses]
        assert a_houses != b_houses

    def test_minor_aspects_included(self, chart_a, chart_b):
        major = calculate_synastry(chart_a, chart_b)
        minor = calculate_synastry(chart_a, chart_b, include_minor_aspects=True)

        assert len(minor.inter_aspects) >= len(major.inter_aspects)

    def test_same_chart_synastry(self, chart_a):
        report = calculate_synastry(chart_a, chart_a)

        assert len(report.inter_aspects) > 0
        for aspect in report.inter_aspects:
            if aspect.planet_a == aspect.planet_b:
                assert aspect.aspect_type == AspectType.CONJUNCTION
                assert aspect.orb < 0.01


class TestInterAspects:
    def test_conjunction_between_charts(self):
        pos_a = RawPosition(
            planet=Planet.VENUS, longitude=100.0, latitude=0.0,
            distance=0.7, speed=1.2, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=10.0,
        )
        pos_b = RawPosition(
            planet=Planet.MARS, longitude=103.0, latitude=0.0,
            distance=1.5, speed=0.5, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=13.0,
        )

        aspects = find_inter_aspects([pos_a], [pos_b])
        assert len(aspects) == 1
        assert aspects[0].aspect_type == AspectType.CONJUNCTION
        assert aspects[0].planet_a == Planet.VENUS
        assert aspects[0].planet_b == Planet.MARS

    def test_south_node_excluded(self):
        pos_a = RawPosition(
            planet=Planet.SOUTH_NODE, longitude=100.0, latitude=0.0,
            distance=0.0, speed=-0.05, is_retrograde=True,
            sign=Sign.CANCER, degree_in_sign=10.0,
        )
        pos_b = RawPosition(
            planet=Planet.SUN, longitude=100.0, latitude=0.0,
            distance=1.0, speed=1.0, is_retrograde=False,
            sign=Sign.CANCER, degree_in_sign=10.0,
        )

        aspects = find_inter_aspects([pos_a], [pos_b])
        assert len(aspects) == 0

    def test_no_aspect_out_of_orb(self):
        pos_a = RawPosition(
            planet=Planet.SATURN, longitude=10.0, latitude=0.0,
            distance=9.5, speed=0.03, is_retrograde=False,
            sign=Sign.ARIES, degree_in_sign=10.0,
        )
        pos_b = RawPosition(
            planet=Planet.SATURN, longitude=60.0, latitude=0.0,
            distance=9.5, speed=0.03, is_retrograde=False,
            sign=Sign.TAURUS, degree_in_sign=30.0,
        )

        aspects = find_inter_aspects([pos_a], [pos_b])
        assert len(aspects) == 0


class TestOverlayPlacements:
    def test_overlay_returns_all_planets(self, chart_a, chart_b):
        placements = compute_overlay(chart_a, chart_b)
        assert len(placements) == 14

        planet_names = {p.planet for p in placements}
        assert Planet.SUN in planet_names
        assert Planet.MOON in planet_names
        assert Planet.PLUTO in planet_names

    def test_overlay_houses_valid(self, chart_a, chart_b):
        placements = compute_overlay(chart_a, chart_b)
        for p in placements:
            assert 1 <= p.overlay_house <= 12


class TestSynastryFormatters:
    def test_to_json(self, chart_a, chart_b):
        report = calculate_synastry(chart_a, chart_b)
        json_str = synastry_to_json(report)
        parsed = json.loads(json_str)

        assert "chart_a" in parsed
        assert "chart_b" in parsed
        assert "inter_aspects" in parsed
        assert "a_in_b_houses" in parsed
        assert "b_in_a_houses" in parsed

    def test_to_dict(self, chart_a, chart_b):
        report = calculate_synastry(chart_a, chart_b)
        d = synastry_to_dict(report)

        assert isinstance(d, dict)
        assert "inter_aspects" in d

    def test_to_markdown(self, chart_a, chart_b):
        report = calculate_synastry(chart_a, chart_b)
        md = synastry_to_markdown(report)

        assert "# Synastry: Person A & Person B" in md
        assert "## Inter-Chart Aspects" in md
        assert "## Person A's Planets in Person B's Houses" in md
        assert "## Person B's Planets in Person A's Houses" in md

    def test_markdown_unnamed_charts(self, chart_a, chart_b):
        chart_a.name = None
        chart_b.name = None
        report = calculate_synastry(chart_a, chart_b)
        md = synastry_to_markdown(report)

        assert "# Synastry: Chart A & Chart B" in md
