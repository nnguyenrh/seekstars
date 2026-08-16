import json
import os
import pytest
from click.testing import CliRunner

from starseek.cli.main import cli
from starseek.config import reset_settings
from starseek.services.storage import init_db, save_chart
from starseek.models.input import BirthData
from starseek.models.enums import HouseSystem
from starseek.core.chart import build_chart
from datetime import datetime


@pytest.fixture(autouse=True)
def clean_settings():
    reset_settings()
    yield
    reset_settings()
    for key in ["GEONAMES_USERNAME", "STARSEEK_DB_PATH", "STARSEEK_EPHE_PATH"]:
        os.environ.pop(key, None)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    os.environ["STARSEEK_DB_PATH"] = path
    init_db(path)
    return path


@pytest.fixture
def sample_chart_in_db(db_path):
    bd = BirthData(
        name="Test Person",
        birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        house_system=HouseSystem.PLACIDUS,
    )
    chart = build_chart(bd)
    chart_id = save_chart(db_path, chart)
    return chart_id


class TestChartCommand:
    def test_chart_with_coordinates(self, runner, tmp_path):
        db_path = str(tmp_path / "chart_test.db")
        os.environ["STARSEEK_DB_PATH"] = db_path

        result = runner.invoke(cli, [
            "chart",
            "--datetime", "2000-01-01T00:00:00",
            "--lat", "0.0",
            "--lng", "0.0",
            "--tz", "UTC",
        ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "planets" in data
        assert len(data["planets"]) == 14

    def test_chart_markdown_format(self, runner, tmp_path):
        db_path = str(tmp_path / "md_test.db")
        os.environ["STARSEEK_DB_PATH"] = db_path

        result = runner.invoke(cli, [
            "chart",
            "--datetime", "2000-01-01T00:00:00",
            "--lat", "0.0",
            "--lng", "0.0",
            "--tz", "UTC",
            "--format", "markdown",
        ])

        assert result.exit_code == 0
        assert "## Planetary Positions" in result.output

    def test_chart_whole_sign(self, runner, tmp_path):
        db_path = str(tmp_path / "ws_test.db")
        os.environ["STARSEEK_DB_PATH"] = db_path

        result = runner.invoke(cli, [
            "chart",
            "--datetime", "2000-01-01T00:00:00",
            "--lat", "0.0",
            "--lng", "0.0",
            "--tz", "UTC",
            "--houses", "whole-sign",
        ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["house_system"] == "Whole Sign"

    def test_chart_save(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart",
            "--datetime", "2000-01-01T00:00:00",
            "--lat", "0.0",
            "--lng", "0.0",
            "--tz", "UTC",
            "--save",
            "--name", "Saved Chart",
        ])

        assert result.exit_code == 0

    def test_chart_missing_location(self, runner):
        result = runner.invoke(cli, [
            "chart",
            "--datetime", "2000-01-01T00:00:00",
        ])

        assert result.exit_code != 0

    def test_chart_invalid_datetime(self, runner):
        result = runner.invoke(cli, [
            "chart",
            "--datetime", "not-a-date",
            "--lat", "0.0",
            "--lng", "0.0",
            "--tz", "UTC",
        ])

        assert result.exit_code != 0


class TestListCommand:
    def test_list_empty(self, runner, db_path):
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "No charts found" in result.output

    def test_list_with_charts(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "Test Person" in result.output

    def test_list_filter(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["list", "--name", "Nonexistent"])
        assert result.exit_code == 0
        assert "No charts found" in result.output


class TestShowCommand:
    def test_show_chart(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["show", str(sample_chart_in_db)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Test Person"

    def test_show_markdown(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["show", str(sample_chart_in_db), "--format", "markdown"])
        assert result.exit_code == 0
        assert "Test Person" in result.output

    def test_show_nonexistent(self, runner, db_path):
        result = runner.invoke(cli, ["show", "9999"])
        assert result.exit_code != 0


class TestDeleteCommand:
    def test_delete_with_confirm(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["delete", str(sample_chart_in_db)], input="y\n")
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_delete_cancel(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["delete", str(sample_chart_in_db)], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output

    def test_delete_force(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["delete", str(sample_chart_in_db), "--yes"])
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_delete_nonexistent(self, runner, db_path):
        result = runner.invoke(cli, ["delete", "9999", "--yes"])
        assert result.exit_code != 0
