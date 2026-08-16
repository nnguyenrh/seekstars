import os
import pytest
from fastapi.testclient import TestClient

from starseek.api.app import create_app
from starseek.api.dependencies import get_settings, get_db_path
from starseek.config import Settings, load_settings, reset_settings
from starseek.services.storage import init_db, save_chart
from starseek.models.input import BirthData
from starseek.models.enums import HouseSystem
from starseek.core.chart import build_chart
from datetime import datetime


@pytest.fixture(autouse=True)
def clean_env():
    reset_settings()
    yield
    reset_settings()
    for key in ["STARSEEK_DB_PATH", "GEONAMES_USERNAME"]:
        os.environ.pop(key, None)


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_api.db")
    init_db(path)
    return path


@pytest.fixture
def app(db_path):
    application = create_app()

    def override_settings():
        s = Settings(db_path=db_path, geonames_username="")
        return s

    def override_db_path():
        return db_path

    application.dependency_overrides[get_settings] = override_settings
    application.dependency_overrides[get_db_path] = override_db_path
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def saved_chart_id(db_path):
    bd = BirthData(
        name="API Test",
        birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
    )
    chart = build_chart(bd)
    return save_chart(db_path, chart)


@pytest.fixture
def second_chart_id(db_path):
    bd = BirthData(
        name="API Test B",
        birth_datetime=datetime(1995, 6, 15, 14, 30, 0),
        latitude=51.5074,
        longitude=-0.1278,
        timezone="Europe/London",
    )
    chart = build_chart(bd)
    return save_chart(db_path, chart)


class TestCreateChart:
    def test_create_with_coordinates(self, client):
        response = client.post("/api/v1/charts", json={
            "name": "Test Chart",
            "birth_datetime": "2000-01-01T00:00:00",
            "latitude": 0.0,
            "longitude": 0.0,
            "timezone": "UTC",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Chart"
        assert len(data["planets"]) == 14
        assert len(data["houses"]) == 12
        assert data["id"] is not None

    def test_create_with_whole_sign(self, client):
        response = client.post("/api/v1/charts", json={
            "birth_datetime": "2000-01-01T00:00:00",
            "latitude": 0.0,
            "longitude": 0.0,
            "timezone": "UTC",
            "house_system": "Whole Sign",
        })
        assert response.status_code == 201
        assert response.json()["house_system"] == "Whole Sign"

    def test_create_missing_location(self, client):
        response = client.post("/api/v1/charts", json={
            "birth_datetime": "2000-01-01T00:00:00",
        })
        assert response.status_code == 422

    def test_create_invalid_latitude(self, client):
        response = client.post("/api/v1/charts", json={
            "birth_datetime": "2000-01-01T00:00:00",
            "latitude": 999.0,
            "longitude": 0.0,
            "timezone": "UTC",
        })
        assert response.status_code == 422


class TestGetCharts:
    def test_list_empty(self, client):
        response = client.get("/api/v1/charts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["charts"] == []

    def test_list_with_chart(self, client, saved_chart_id):
        response = client.get("/api/v1/charts")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["charts"][0]["id"] == saved_chart_id

    def test_list_filter_by_name(self, client, saved_chart_id):
        response = client.get("/api/v1/charts", params={"name": "API Test"})
        assert response.status_code == 200
        assert response.json()["total"] == 1

        response = client.get("/api/v1/charts", params={"name": "Nonexistent"})
        assert response.json()["total"] == 0

    def test_list_pagination(self, client, db_path):
        for i in range(5):
            bd = BirthData(
                name=f"Chart {i}",
                birth_datetime=datetime(2000, 1, 1, 0, 0, 0),
                latitude=0.0, longitude=0.0, timezone="UTC",
            )
            save_chart(db_path, build_chart(bd))

        response = client.get("/api/v1/charts", params={"limit": 2, "offset": 0})
        data = response.json()
        assert data["total"] == 5
        assert len(data["charts"]) == 2


class TestGetChart:
    def test_get_existing(self, client, saved_chart_id):
        response = client.get(f"/api/v1/charts/{saved_chart_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "API Test"
        assert len(data["planets"]) == 14

    def test_get_by_name(self, client, saved_chart_id):
        response = client.get("/api/v1/charts/API Test")
        assert response.status_code == 200
        assert response.json()["name"] == "API Test"

    def test_get_nonexistent(self, client):
        response = client.get("/api/v1/charts/9999")
        assert response.status_code == 404


class TestChartNameConflict:
    def test_duplicate_name_rejected(self, client, saved_chart_id):
        response = client.post("/api/v1/charts", json={
            "name": "API Test",
            "birth_datetime": "1990-06-15T12:00:00",
            "latitude": 51.5,
            "longitude": -0.1,
            "timezone": "Europe/London",
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_duplicate_name_overwrite(self, client, saved_chart_id):
        response = client.post(
            "/api/v1/charts",
            json={
                "name": "API Test",
                "birth_datetime": "1990-06-15T12:00:00",
                "latitude": 51.5,
                "longitude": -0.1,
                "timezone": "Europe/London",
            },
            params={"overwrite": True},
        )
        assert response.status_code == 201
        assert response.json()["id"] == saved_chart_id


class TestDeleteChart:
    def test_delete_existing(self, client, saved_chart_id):
        response = client.delete(f"/api/v1/charts/{saved_chart_id}")
        assert response.status_code == 204

        response = client.get(f"/api/v1/charts/{saved_chart_id}")
        assert response.status_code == 404

    def test_delete_nonexistent(self, client):
        response = client.delete("/api/v1/charts/9999")
        assert response.status_code == 404


class TestGetChartMarkdown:
    def test_markdown_response(self, client, saved_chart_id):
        response = client.get(f"/api/v1/charts/{saved_chart_id}/markdown")
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "## Planetary Positions" in response.text

    def test_markdown_nonexistent(self, client):
        response = client.get("/api/v1/charts/9999/markdown")
        assert response.status_code == 404


class TestHealthCheck:
    def test_health(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["ephemeris_initialized"] is True
        assert data["database_connected"] is True


class TestGeocodeEndpoint:
    def test_geocode_no_username(self, client):
        response = client.post("/api/v1/geocode", json={"city": "New York"})
        assert response.status_code == 400
        assert "not configured" in response.json()["detail"]

    def test_geocode_empty_city(self, client):
        response = client.post("/api/v1/geocode", json={"city": ""})
        assert response.status_code == 422


class TestTransitsEndpoint:
    def test_transits_default_time(self, client, saved_chart_id):
        response = client.post(f"/api/v1/charts/{saved_chart_id}/transits")
        assert response.status_code == 200
        data = response.json()
        assert "transit_positions" in data
        assert "transit_aspects" in data
        assert len(data["transit_positions"]) == 14

    def test_transits_specific_time(self, client, saved_chart_id):
        response = client.post(
            f"/api/v1/charts/{saved_chart_id}/transits",
            json={"transit_datetime": "2026-06-15T12:00:00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "2026-06-15" in data["transit_datetime"]
        assert len(data["transit_positions"]) == 14

    def test_transits_with_minor_aspects(self, client, saved_chart_id):
        major = client.post(
            f"/api/v1/charts/{saved_chart_id}/transits",
            json={"transit_datetime": "2026-06-15T12:00:00"},
        ).json()
        minor = client.post(
            f"/api/v1/charts/{saved_chart_id}/transits",
            json={
                "transit_datetime": "2026-06-15T12:00:00",
                "include_minor_aspects": True,
            },
        ).json()
        assert len(minor["transit_aspects"]) >= len(major["transit_aspects"])

    def test_transits_nonexistent_chart(self, client):
        response = client.post("/api/v1/charts/9999/transits")
        assert response.status_code == 404

    def test_transits_has_natal_info(self, client, saved_chart_id):
        response = client.post(f"/api/v1/charts/{saved_chart_id}/transits")
        data = response.json()
        assert data["natal_chart_id"] == saved_chart_id
        assert data["natal_name"] == "API Test"

    def test_transits_by_name(self, client, saved_chart_id):
        response = client.post("/api/v1/charts/API Test/transits")
        assert response.status_code == 200
        assert response.json()["natal_name"] == "API Test"


class TestSynastryEndpoint:
    def test_synastry(self, client, saved_chart_id, second_chart_id):
        response = client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": str(second_chart_id),
        })
        assert response.status_code == 201
        data = response.json()
        assert "inter_aspects" in data
        assert "a_in_b_houses" in data
        assert "b_in_a_houses" in data
        assert data["chart_a"]["name"] == "API Test"
        assert data["chart_b"]["name"] == "API Test B"

    def test_synastry_by_name(self, client, saved_chart_id, second_chart_id):
        response = client.post("/api/v1/synastry", json={
            "chart_a": "API Test",
            "chart_b": "API Test B",
        })
        assert response.status_code == 201
        assert response.json()["chart_a"]["name"] == "API Test"

    def test_synastry_with_minor_aspects(self, client, saved_chart_id, second_chart_id):
        major = client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": str(second_chart_id),
        }).json()
        minor = client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": str(second_chart_id),
            "include_minor_aspects": True,
        }).json()
        assert len(minor["inter_aspects"]) >= len(major["inter_aspects"])

    def test_synastry_nonexistent_chart_a(self, client, second_chart_id):
        response = client.post("/api/v1/synastry", json={
            "chart_a": "9999",
            "chart_b": str(second_chart_id),
        })
        assert response.status_code == 404

    def test_synastry_nonexistent_chart_b(self, client, saved_chart_id):
        response = client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": "9999",
        })
        assert response.status_code == 404

    def test_synastry_overlay_counts(self, client, saved_chart_id, second_chart_id):
        data = client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": str(second_chart_id),
        }).json()
        assert len(data["a_in_b_houses"]) == 14
        assert len(data["b_in_a_houses"]) == 14

    def test_synastry_saves_by_default(self, client, saved_chart_id, second_chart_id):
        client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": str(second_chart_id),
        })
        response = client.get("/api/v1/synastry")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_synastry_no_save(self, client, saved_chart_id, second_chart_id):
        client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": str(second_chart_id),
            "save": False,
        })
        response = client.get("/api/v1/synastry")
        assert response.json()["total"] == 0


class TestSynastryPersistenceEndpoints:
    def _create_synastry(self, client, saved_chart_id, second_chart_id):
        client.post("/api/v1/synastry", json={
            "chart_a": str(saved_chart_id),
            "chart_b": str(second_chart_id),
        })

    def test_list_synastries(self, client, saved_chart_id, second_chart_id):
        self._create_synastry(client, saved_chart_id, second_chart_id)
        response = client.get("/api/v1/synastry")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["reports"][0]["name_a"] == "API Test"
        assert data["reports"][0]["name_b"] == "API Test B"

    def test_get_synastry(self, client, saved_chart_id, second_chart_id):
        self._create_synastry(client, saved_chart_id, second_chart_id)
        response = client.get("/api/v1/synastry/1")
        assert response.status_code == 200
        data = response.json()
        assert "inter_aspects" in data

    def test_get_synastry_nonexistent(self, client):
        response = client.get("/api/v1/synastry/9999")
        assert response.status_code == 404

    def test_delete_synastry(self, client, saved_chart_id, second_chart_id):
        self._create_synastry(client, saved_chart_id, second_chart_id)
        response = client.delete("/api/v1/synastry/1")
        assert response.status_code == 204

        response = client.get("/api/v1/synastry/1")
        assert response.status_code == 404

    def test_delete_synastry_nonexistent(self, client):
        response = client.delete("/api/v1/synastry/9999")
        assert response.status_code == 404
