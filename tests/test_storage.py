import os
import pytest
import tempfile
from datetime import datetime

from starseek.services.storage import (
    init_db, save_chart, load_chart, list_charts, delete_chart,
    save_synastry, load_synastry, list_synastries, delete_synastry,
    cache_location, get_cached_location, ChartListItem, SynastryListItem,
)
from starseek.services.geocoding import GeocodingResult
from starseek.models.enums import HouseSystem
from starseek.models.input import BirthData
from starseek.core.chart import build_chart
from starseek.core.synastry import calculate_synastry


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def sample_chart():
    bd = BirthData(
        name="Test Person",
        birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        house_system=HouseSystem.PLACIDUS,
    )
    return build_chart(bd)


class TestInitDb:
    def test_creates_database(self, tmp_path):
        path = str(tmp_path / "new.db")
        init_db(path)
        assert os.path.exists(path)

    def test_creates_admin_user(self, tmp_path):
        import sqlite3
        path = str(tmp_path / "new.db")
        init_db(path)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
        conn.close()
        assert row is not None
        assert row["role"] == "admin"

    def test_force_reset(self, db_path, sample_chart):
        save_chart(db_path, sample_chart)
        items, total = list_charts(db_path)
        assert total == 1

        init_db(db_path, force=True)
        items, total = list_charts(db_path)
        assert total == 0

    def test_idempotent(self, tmp_path):
        path = str(tmp_path / "new.db")
        init_db(path)
        init_db(path)
        import sqlite3
        conn = sqlite3.connect(path)
        count = conn.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0]
        conn.close()
        assert count == 1


class TestChartCRUD:
    def test_save_and_load(self, db_path, sample_chart):
        chart_id = save_chart(db_path, sample_chart)
        assert chart_id > 0

        loaded = load_chart(db_path, chart_id)
        assert loaded is not None
        assert loaded.id == chart_id
        assert loaded.name == "Test Person"
        assert len(loaded.planets) == 14

    def test_load_nonexistent(self, db_path):
        result = load_chart(db_path, 9999)
        assert result is None

    def test_list_charts(self, db_path, sample_chart):
        save_chart(db_path, sample_chart)
        save_chart(db_path, sample_chart)

        items, total = list_charts(db_path)
        assert total == 2
        assert len(items) == 2
        assert isinstance(items[0], ChartListItem)

    def test_list_with_filter(self, db_path, sample_chart):
        save_chart(db_path, sample_chart)

        items, total = list_charts(db_path, name_filter="Test")
        assert total == 1

        items, total = list_charts(db_path, name_filter="Nonexistent")
        assert total == 0

    def test_list_pagination(self, db_path, sample_chart):
        for _ in range(5):
            save_chart(db_path, sample_chart)

        items, total = list_charts(db_path, limit=2, offset=0)
        assert total == 5
        assert len(items) == 2

        items, total = list_charts(db_path, limit=2, offset=4)
        assert len(items) == 1

    def test_delete_chart(self, db_path, sample_chart):
        chart_id = save_chart(db_path, sample_chart)
        assert delete_chart(db_path, chart_id) is True
        assert load_chart(db_path, chart_id) is None

    def test_delete_nonexistent(self, db_path):
        assert delete_chart(db_path, 9999) is False


class TestLocationCache:
    def test_cache_and_retrieve(self, db_path):
        result = GeocodingResult(
            city_name="New York City, New York, United States",
            country="United States",
            country_code="US",
            latitude=40.7128,
            longitude=-74.006,
            timezone="America/New_York",
        )

        cache_location(db_path, "New York", result)
        cached = get_cached_location(db_path, "New York")

        assert cached is not None
        assert cached.latitude == pytest.approx(40.7128)
        assert cached.longitude == pytest.approx(-74.006)
        assert cached.timezone == "America/New_York"

    def test_cache_case_insensitive(self, db_path):
        result = GeocodingResult(
            city_name="Tokyo",
            country="Japan",
            country_code="JP",
            latitude=35.6762,
            longitude=139.6503,
            timezone="Asia/Tokyo",
        )

        cache_location(db_path, "Tokyo", result)
        cached = get_cached_location(db_path, "tokyo")
        assert cached is not None

    def test_cache_miss(self, db_path):
        cached = get_cached_location(db_path, "Nonexistent")
        assert cached is None

    def test_cache_overwrite(self, db_path):
        result1 = GeocodingResult(
            city_name="London, England",
            country="UK", country_code="GB",
            latitude=51.5, longitude=-0.12, timezone="Europe/London",
        )
        result2 = GeocodingResult(
            city_name="London, Ohio",
            country="US", country_code="US",
            latitude=39.8, longitude=-83.4, timezone="America/New_York",
        )

        cache_location(db_path, "london", result1)
        cache_location(db_path, "london", result2)

        cached = get_cached_location(db_path, "london")
        assert cached.latitude == pytest.approx(39.8)


class TestSynastryCRUD:
    @pytest.fixture
    def two_charts(self, db_path, sample_chart):
        bd2 = BirthData(
            name="Second Person",
            birth_datetime=datetime(1995, 6, 15, 14, 30, 0),
            latitude=51.5074,
            longitude=-0.1278,
            timezone="Europe/London",
            house_system=HouseSystem.PLACIDUS,
        )
        chart_b = build_chart(bd2)
        id_a = save_chart(db_path, sample_chart)
        id_b = save_chart(db_path, chart_b)
        chart_a = load_chart(db_path, id_a)
        chart_b = load_chart(db_path, id_b)
        return chart_a, chart_b

    def test_save_and_load(self, db_path, two_charts):
        chart_a, chart_b = two_charts
        report = calculate_synastry(chart_a, chart_b)
        report_id = save_synastry(db_path, report)
        assert report_id > 0

        loaded = load_synastry(db_path, report_id)
        assert loaded is not None
        assert loaded.chart_a.name == "Test Person"
        assert loaded.chart_b.name == "Second Person"
        assert len(loaded.inter_aspects) > 0
        assert len(loaded.a_in_b_houses) == 14

    def test_load_nonexistent(self, db_path):
        assert load_synastry(db_path, 9999) is None

    def test_list_synastries(self, db_path, two_charts):
        chart_a, chart_b = two_charts
        report = calculate_synastry(chart_a, chart_b)
        save_synastry(db_path, report)
        save_synastry(db_path, report)

        items, total = list_synastries(db_path)
        assert total == 2
        assert len(items) == 2
        assert isinstance(items[0], SynastryListItem)
        assert items[0].name_a == "Test Person"
        assert items[0].name_b == "Second Person"

    def test_list_empty(self, db_path):
        items, total = list_synastries(db_path)
        assert total == 0

    def test_delete_synastry(self, db_path, two_charts):
        chart_a, chart_b = two_charts
        report = calculate_synastry(chart_a, chart_b)
        report_id = save_synastry(db_path, report)
        assert delete_synastry(db_path, report_id) is True
        assert load_synastry(db_path, report_id) is None

    def test_delete_nonexistent(self, db_path):
        assert delete_synastry(db_path, 9999) is False
