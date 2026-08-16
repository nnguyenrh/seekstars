"""SVG chart rendering using Kerykeion's ChartDrawer."""

from typing import Optional, Literal

from kerykeion import ChartDataFactory, ChartDrawer

from starseek.models.chart import BirthChart
from starseek_charts.adapter import birthchart_to_subject


ThemeName = Literal[
    "light", "dark", "dark-high-contrast", "classic",
    "strawberry", "black-and-white",
]


def render_natal_svg(
    chart: BirthChart,
    theme: ThemeName = "classic",
) -> str:
    subject = birthchart_to_subject(chart)
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    drawer = ChartDrawer(chart_data, theme=theme)
    return drawer.generate_svg_string()


def render_transit_svg(
    natal_chart: BirthChart,
    transit_chart: BirthChart,
    theme: ThemeName = "classic",
) -> str:
    natal_subject = birthchart_to_subject(natal_chart)
    transit_subject = birthchart_to_subject(transit_chart)
    chart_data = ChartDataFactory.create_transit_chart_data(
        natal_subject, transit_subject
    )
    drawer = ChartDrawer(chart_data, theme=theme)
    return drawer.generate_svg_string()


def render_synastry_svg(
    chart_a: BirthChart,
    chart_b: BirthChart,
    theme: ThemeName = "classic",
) -> str:
    subject_a = birthchart_to_subject(chart_a)
    subject_b = birthchart_to_subject(chart_b)
    chart_data = ChartDataFactory.create_synastry_chart_data(
        subject_a, subject_b
    )
    drawer = ChartDrawer(chart_data, theme=theme)
    return drawer.generate_svg_string()


def render_svg(
    chart: BirthChart,
    chart_b: Optional[BirthChart] = None,
    chart_type: str = "natal",
    theme: ThemeName = "classic",
) -> str:
    if chart_type == "natal" or chart_b is None:
        return render_natal_svg(chart, theme=theme)
    elif chart_type == "transit":
        return render_transit_svg(chart, chart_b, theme=theme)
    elif chart_type == "synastry":
        return render_synastry_svg(chart, chart_b, theme=theme)
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")
