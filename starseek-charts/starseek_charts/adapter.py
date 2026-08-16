"""Adapter to convert StarSeek BirthChart models to Kerykeion subjects."""

from kerykeion import AstrologicalSubjectFactory
from kerykeion.schemas.kr_models import AstrologicalSubjectModel

from starseek.models.chart import BirthChart


HOUSE_SYSTEM_MAP = {
    "Placidus": "P",
    "Whole Sign": "W",
}


def birthchart_to_subject(chart: BirthChart) -> AstrologicalSubjectModel:
    dt = chart.birth_datetime
    hs = HOUSE_SYSTEM_MAP.get(chart.house_system.value, "P")

    return AstrologicalSubjectFactory.from_birth_data(
        name=chart.name or "Chart",
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        seconds=dt.second,
        lat=chart.latitude,
        lng=chart.longitude,
        tz_str=chart.timezone,
        online=False,
        houses_system_identifier=hs,
    )
