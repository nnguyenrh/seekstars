import pytest
from datetime import datetime

from starseek.models.enums import Planet, Sign, HouseSystem, Element, Modality
from starseek.models.input import BirthData
from starseek.core.chart import build_chart

from tests.conftest import _make_birth_data


class TestChartBuilder:
    def test_null_island_chart(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        assert len(chart.planets) == 14
        assert len(chart.houses) == 12
        assert len(chart.aspects) > 0
        assert chart.summary is not None

    def test_sun_position_accuracy(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        fix_sun = next(p for p in fixture["planets"] if p["name"] == "Sun")
        chart_sun = next(p for p in chart.planets if p.planet == Planet.SUN)

        assert abs(chart_sun.longitude - fix_sun["longitude"]) < 0.001
        assert chart_sun.sign == Sign.CAPRICORN

    def test_moon_position_accuracy(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        fix_moon = next(p for p in fixture["planets"] if p["name"] == "Moon")
        chart_moon = next(p for p in chart.planets if p.planet == Planet.MOON)

        assert abs(chart_moon.longitude - fix_moon["longitude"]) < 0.001

    def test_diana_chart(self, reference_charts):
        fixture = reference_charts["princess_diana"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        sun = next(p for p in chart.planets if p.planet == Planet.SUN)
        moon = next(p for p in chart.planets if p.planet == Planet.MOON)

        assert sun.sign == Sign.CANCER
        assert 9 < sun.sign_degree < 10
        assert moon.sign == Sign.AQUARIUS
        assert 24 < moon.sign_degree < 26

    def test_diana_ascendant(self, reference_charts):
        fixture = reference_charts["princess_diana"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        assert chart.houses[0].sign == Sign.SAGITTARIUS

    def test_retrograde_planets(self, reference_charts):
        fixture = reference_charts["retrograde_heavy"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        saturn = next(p for p in chart.planets if p.planet == Planet.SATURN)
        neptune = next(p for p in chart.planets if p.planet == Planet.NEPTUNE)
        pluto = next(p for p in chart.planets if p.planet == Planet.PLUTO)

        assert saturn.is_retrograde
        assert neptune.is_retrograde
        assert pluto.is_retrograde

    def test_midnight_boundary_correct_sign(self, reference_charts):
        fixture = reference_charts["midnight_boundary"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        sun = next(p for p in chart.planets if p.planet == Planet.SUN)
        assert sun.sign == Sign.CAPRICORN

    def test_element_counts(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        total = sum(chart.summary.element_counts.values())
        assert total == 10

    def test_modality_counts(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        total = sum(chart.summary.modality_counts.values())
        assert total == 10

    def test_whole_sign_houses(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"], hs=HouseSystem.WHOLE_SIGN)
        chart = build_chart(bd)

        signs = [h.sign for h in chart.houses]
        assert len(set(signs)) == 12

    def test_chart_has_dignity(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        for p in chart.planets:
            assert p.dignity is not None

    def test_sign_minutes(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)

        for p in chart.planets:
            assert 0 <= p.sign_minute < 60
