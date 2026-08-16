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
    os.environ["GEONAMES_USERNAME"] = "nhing"
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


@pytest.fixture
def second_chart_in_db(db_path):
    bd = BirthData(
        name="Second Person",
        birth_datetime=datetime(1995, 6, 15, 14, 30, 0),
        latitude=51.5074,
        longitude=-0.1278,
        timezone="Europe/London",
        house_system=HouseSystem.PLACIDUS,
    )
    chart = build_chart(bd)
    chart_id = save_chart(db_path, chart)
    return chart_id


class TestChartCommand:
    def test_chart_with_city(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart",
            "--date", "2000-01-01",
            "--time", "00:00",
            "--city", "New York",
            "--quiet",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "planets" in data
        assert len(data["planets"]) == 14

    def test_chart_markdown_format(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart",
            "--date", "2000-01-01",
            "--time", "00:00",
            "--city", "New York",
            "--format", "markdown",
        ])
        assert result.exit_code == 0
        assert "## Planetary Positions" in result.output

    def test_chart_whole_sign(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart",
            "--date", "2000-01-01",
            "--time", "00:00",
            "--city", "New York",
            "--houses", "whole-sign",
            "--quiet",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["house_system"] == "Whole Sign"

    def test_chart_save(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart",
            "--date", "2000-01-01",
            "--time", "00:00",
            "--city", "New York",
            "--save",
            "--name", "Saved Chart",
        ])
        assert result.exit_code == 0

    def test_chart_invalid_date(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart",
            "--date", "not-a-date",
            "--time", "12:00",
            "--city", "New York",
        ])
        assert result.exit_code != 0

    def test_chart_invalid_time(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart",
            "--date", "2000-01-01",
            "--time", "99:99",
            "--city", "New York",
        ])
        assert result.exit_code != 0


class TestChartManualCommand:
    def test_chart_manual(self, runner, db_path):
        result = runner.invoke(cli, [
            "chart-manual",
            "--datetime", "2000-01-01T00:00:00",
            "--lat", "0.0",
            "--lng", "0.0",
            "--tz", "UTC",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["planets"]) == 14


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


class TestTransitsCommand:
    def test_transits_json(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, [
            "transits", str(sample_chart_in_db),
            "--date", "2026-06-15",
            "--time", "12:00",
            "--quiet",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "transit_positions" in data
        assert "transit_aspects" in data
        assert len(data["transit_positions"]) == 14

    def test_transits_markdown(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, [
            "transits", str(sample_chart_in_db),
            "--date", "2026-06-15",
            "--time", "12:00",
            "--format", "markdown",
        ])
        assert result.exit_code == 0
        assert "## Current Planetary Positions" in result.output
        assert "## Transit-to-Natal Aspects" in result.output

    def test_transits_default_time(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, [
            "transits", str(sample_chart_in_db), "--quiet",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["transit_positions"]) == 14

    def test_transits_date_only(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, [
            "transits", str(sample_chart_in_db),
            "--date", "2026-06-15",
            "--quiet",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "2026-06-15" in data["transit_datetime"]

    def test_transits_nonexistent_chart(self, runner, db_path):
        result = runner.invoke(cli, ["transits", "9999", "--quiet"])
        assert result.exit_code != 0
        assert "not found" in result.output


class TestSynastryCommand:
    def test_synastry_json(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        result = runner.invoke(cli, [
            "synastry", str(sample_chart_in_db), str(second_chart_in_db),
            "--quiet",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "inter_aspects" in data
        assert "a_in_b_houses" in data
        assert "b_in_a_houses" in data

    def test_synastry_markdown(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        result = runner.invoke(cli, [
            "synastry", str(sample_chart_in_db), str(second_chart_in_db),
            "--format", "markdown",
        ])
        assert result.exit_code == 0
        assert "## Inter-Chart Aspects" in result.output
        assert "Houses" in result.output

    def test_synastry_nonexistent_chart_a(self, runner, db_path, second_chart_in_db):
        result = runner.invoke(cli, ["synastry", "9999", str(second_chart_in_db), "--quiet"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_synastry_nonexistent_chart_b(self, runner, db_path, sample_chart_in_db):
        result = runner.invoke(cli, ["synastry", str(sample_chart_in_db), "9999", "--quiet"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_synastry_save(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        result = runner.invoke(cli, [
            "synastry", str(sample_chart_in_db), str(second_chart_in_db),
            "--save", "--quiet",
        ])
        assert result.exit_code == 0

        result = runner.invoke(cli, ["list-synastry"])
        assert result.exit_code == 0
        assert "Test Person" in result.output
        assert "Second Person" in result.output


class TestSynastryPersistenceCommands:
    def _save_synastry(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        runner.invoke(cli, [
            "synastry", str(sample_chart_in_db), str(second_chart_in_db),
            "--save", "--quiet",
        ])

    def test_list_synastry_empty(self, runner, db_path):
        result = runner.invoke(cli, ["list-synastry"])
        assert result.exit_code == 0
        assert "No synastry reports found" in result.output

    def test_show_synastry(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        self._save_synastry(runner, db_path, sample_chart_in_db, second_chart_in_db)
        result = runner.invoke(cli, ["show-synastry", "1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "inter_aspects" in data

    def test_show_synastry_markdown(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        self._save_synastry(runner, db_path, sample_chart_in_db, second_chart_in_db)
        result = runner.invoke(cli, ["show-synastry", "1", "--format", "markdown"])
        assert result.exit_code == 0
        assert "## Inter-Chart Aspects" in result.output

    def test_show_synastry_nonexistent(self, runner, db_path):
        result = runner.invoke(cli, ["show-synastry", "9999"])
        assert result.exit_code != 0

    def test_delete_synastry(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        self._save_synastry(runner, db_path, sample_chart_in_db, second_chart_in_db)
        result = runner.invoke(cli, ["delete-synastry", "1", "--yes"])
        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_delete_synastry_cancel(self, runner, db_path, sample_chart_in_db, second_chart_in_db):
        self._save_synastry(runner, db_path, sample_chart_in_db, second_chart_in_db)
        result = runner.invoke(cli, ["delete-synastry", "1"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output
