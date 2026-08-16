import json
import os
from pathlib import Path

import pytest
from datetime import datetime

from starseek.models.enums import Planet, Sign, HouseSystem
from starseek.models.input import BirthData
from starseek.core.chart import build_chart

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "reference_charts.json"


@pytest.fixture(scope="session")
def reference_charts():
    with open(FIXTURES_PATH) as f:
        return {c["label"]: c for c in json.load(f)}


def _make_birth_data(chart_input: dict, hs: HouseSystem = HouseSystem.PLACIDUS) -> BirthData:
    year = chart_input["year"]
    month = chart_input["month"]
    day = chart_input["day"]
    hour = int(chart_input["hour_utc"])
    minute = int((chart_input["hour_utc"] - hour) * 60)
    second = int(((chart_input["hour_utc"] - hour) * 60 - minute) * 60)

    return BirthData(
        birth_datetime=datetime(year, month, day, hour, minute, second),
        latitude=chart_input["lat"],
        longitude=chart_input["lng"],
        timezone="UTC",
        house_system=hs,
    )
