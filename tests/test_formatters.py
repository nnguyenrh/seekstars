import pytest
from datetime import datetime

from starseek.models.enums import Planet, Sign, HouseSystem
from starseek.models.input import BirthData
from starseek.core.chart import build_chart
from starseek.formatters.json_fmt import to_json, to_dict
from starseek.formatters.markdown_fmt import to_markdown

from tests.conftest import _make_birth_data


class TestJsonFormatter:
    def test_produces_valid_json(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)
        json_str = to_json(chart)
        assert '"planets"' in json_str
        assert '"houses"' in json_str
        assert '"aspects"' in json_str

    def test_to_dict(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)
        d = to_dict(chart)
        assert isinstance(d, dict)
        assert "planets" in d
        assert len(d["planets"]) == 14


class TestMarkdownFormatter:
    def test_produces_markdown(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)
        md = to_markdown(chart)
        assert "## Planetary Positions" in md
        assert "## House Cusps" in md
        assert "## Aspects" in md
        assert "## Summary" in md

    def test_contains_planet_data(self, reference_charts):
        fixture = reference_charts["null_island"]
        bd = _make_birth_data(fixture["input"])
        chart = build_chart(bd)
        md = to_markdown(chart)
        assert "Sun" in md
        assert "Moon" in md
        assert "Capricorn" in md
