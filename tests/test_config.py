import os
import pytest

from starseek.config import load_settings, reset_settings, Settings
from starseek.models.enums import HouseSystem


class TestConfig:
    def setup_method(self):
        reset_settings()

    def teardown_method(self):
        reset_settings()
        for key in ["GEONAMES_USERNAME", "STARSEEK_HOST", "STARSEEK_PORT",
                     "STARSEEK_DB_PATH", "STARSEEK_EPHE_PATH",
                     "STARSEEK_DEFAULT_HOUSE_SYSTEM", "STARSEEK_LOG_LEVEL",
                     "STARSEEK_ADMIN_PASSWORD"]:
            os.environ.pop(key, None)

    def test_defaults(self):
        s = load_settings()
        assert s.geonames_username == ""
        assert s.host == "0.0.0.0"
        assert s.port == 8000
        assert s.default_house_system == HouseSystem.PLACIDUS
        assert s.log_level == "INFO"
        assert s.admin_password == "admin"

    def test_env_override(self):
        os.environ["GEONAMES_USERNAME"] = "testuser"
        os.environ["STARSEEK_PORT"] = "9000"
        os.environ["STARSEEK_DEFAULT_HOUSE_SYSTEM"] = "Whole Sign"

        s = load_settings()
        assert s.geonames_username == "testuser"
        assert s.port == 9000
        assert s.default_house_system == HouseSystem.WHOLE_SIGN

    def test_invalid_house_system_falls_back(self):
        os.environ["STARSEEK_DEFAULT_HOUSE_SYSTEM"] = "InvalidSystem"
        s = load_settings()
        assert s.default_house_system == HouseSystem.PLACIDUS

    def test_orbs_default(self):
        s = load_settings()
        assert len(s.orbs) == 9
