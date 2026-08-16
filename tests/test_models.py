import pytest
from pydantic import ValidationError
from datetime import datetime

from starseek.models.enums import Planet, Sign, HouseSystem, Element, Modality
from starseek.models.input import BirthData
from starseek.models.chart import PlanetPosition, HouseCusp, Aspect, ChartSummary, BirthChart
from starseek.models.user import UserCreate, User, UserLogin


class TestEnums:
    def test_all_planets(self):
        assert len(Planet) == 14

    def test_all_signs(self):
        assert len(Sign) == 12

    def test_planet_str_value(self):
        assert Planet.SUN.value == "Sun"

    def test_sign_str_value(self):
        assert Sign.ARIES.value == "Aries"


class TestBirthData:
    def test_valid_with_coords(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1),
            latitude=0.0,
            longitude=0.0,
            timezone="UTC",
        )
        assert bd.latitude == 0.0

    def test_valid_with_city(self):
        bd = BirthData(
            birth_datetime=datetime(2000, 1, 1),
            city="New York",
        )
        assert bd.city == "New York"

    def test_invalid_no_location(self):
        with pytest.raises(ValidationError):
            BirthData(birth_datetime=datetime(2000, 1, 1))

    def test_latitude_bounds(self):
        with pytest.raises(ValidationError):
            BirthData(
                birth_datetime=datetime(2000, 1, 1),
                latitude=91.0,
                longitude=0.0,
                timezone="UTC",
            )


class TestPlanetPosition:
    def test_valid_position(self):
        pp = PlanetPosition(
            planet=Planet.SUN,
            longitude=280.0,
            latitude=0.0,
            speed=0.95,
            is_retrograde=False,
            sign=Sign.CAPRICORN,
            sign_degree=10.0,
            sign_minute=30,
            house=4,
            dignity=None,
        )
        assert pp.planet == Planet.SUN


class TestUserModels:
    def test_user_create_min_length(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", password="12345678")

    def test_user_create_valid(self):
        u = UserCreate(username="testuser", password="securepass")
        assert u.username == "testuser"
