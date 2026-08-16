import pytest
from datetime import datetime

from starseek.models.input import BirthData
from starseek.models.enums import HouseSystem
from starseek.core.chart import build_chart
from starseek_charts.adapter import birthchart_to_subject
from starseek_charts.svg import (
    render_natal_svg, render_transit_svg, render_synastry_svg, render_svg,
)


@pytest.fixture
def chart_a():
    bd = BirthData(
        name="Person A",
        birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
        latitude=0.0, longitude=0.0, timezone="UTC",
    )
    return build_chart(bd)


@pytest.fixture
def chart_b():
    bd = BirthData(
        name="Person B",
        birth_datetime=datetime(1995, 6, 15, 14, 30, 0),
        latitude=51.5074, longitude=-0.1278, timezone="Europe/London",
    )
    return build_chart(bd)


class TestAdapter:
    def test_birthchart_to_subject(self, chart_a):
        subject = birthchart_to_subject(chart_a)
        assert subject.name == "Person A"
        assert subject.sun is not None
        assert subject.moon is not None

    def test_unnamed_chart(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
            latitude=0.0, longitude=0.0, timezone="UTC",
        )
        chart = build_chart(bd)
        subject = birthchart_to_subject(chart)
        assert subject.name == "Chart"


class TestNatalSVG:
    def test_renders_svg_string(self, chart_a):
        svg = render_natal_svg(chart_a)
        assert isinstance(svg, str)
        assert len(svg) > 1000
        assert "<svg" in svg or "<?xml" in svg

    def test_theme_option(self, chart_a):
        svg = render_natal_svg(chart_a, theme="dark")
        assert isinstance(svg, str)
        assert len(svg) > 1000


class TestTransitSVG:
    def test_renders_dual_wheel(self, chart_a, chart_b):
        svg = render_transit_svg(chart_a, chart_b)
        assert isinstance(svg, str)
        assert len(svg) > 1000


class TestSynastrySVG:
    def test_renders_dual_wheel(self, chart_a, chart_b):
        svg = render_synastry_svg(chart_a, chart_b)
        assert isinstance(svg, str)
        assert len(svg) > 1000


class TestRenderSVG:
    def test_natal_default(self, chart_a):
        svg = render_svg(chart_a)
        assert len(svg) > 1000

    def test_natal_explicit(self, chart_a):
        svg = render_svg(chart_a, chart_type="natal")
        assert len(svg) > 1000

    def test_transit_type(self, chart_a, chart_b):
        svg = render_svg(chart_a, chart_b, chart_type="transit")
        assert len(svg) > 1000

    def test_synastry_type(self, chart_a, chart_b):
        svg = render_svg(chart_a, chart_b, chart_type="synastry")
        assert len(svg) > 1000

    def test_unknown_type_raises(self, chart_a, chart_b):
        with pytest.raises(ValueError, match="Unknown chart type"):
            render_svg(chart_a, chart_b, chart_type="bogus")
