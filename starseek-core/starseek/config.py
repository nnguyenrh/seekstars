import os
from pathlib import Path
from dataclasses import dataclass, field

from dotenv import load_dotenv

from starseek.models.enums import HouseSystem, AspectType


_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    geonames_username: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = str(_PROJECT_ROOT / "starseek.db")
    ephe_path: str = str(_PROJECT_ROOT / "data" / "ephe")
    default_house_system: HouseSystem = HouseSystem.WHOLE_SIGN
    log_level: str = "INFO"
    admin_password: str = "admin"

    orbs: dict[AspectType, float] = field(default_factory=lambda: {
        AspectType.CONJUNCTION: 8.0,
        AspectType.SEXTILE: 6.0,
        AspectType.SQUARE: 7.0,
        AspectType.TRINE: 8.0,
        AspectType.OPPOSITION: 8.0,
        AspectType.SEMI_SEXTILE: 2.0,
        AspectType.SEMI_SQUARE: 2.0,
        AspectType.SESQUIQUADRATE: 2.0,
        AspectType.QUINCUNX: 3.0,
    })


def load_settings(env_file: str | None = None) -> Settings:
    if env_file:
        load_dotenv(env_file)
    else:
        default_env = _PROJECT_ROOT / ".env"
        if default_env.exists():
            load_dotenv(default_env)

    house_str = os.getenv("STARSEEK_DEFAULT_HOUSE_SYSTEM", "Whole Sign")
    try:
        house_system = HouseSystem(house_str)
    except ValueError:
        house_system = HouseSystem.WHOLE_SIGN

    return Settings(
        geonames_username=os.getenv("GEONAMES_USERNAME", ""),
        host=os.getenv("STARSEEK_HOST", "0.0.0.0"),
        port=int(os.getenv("STARSEEK_PORT", "8000")),
        db_path=os.getenv("STARSEEK_DB_PATH", str(_PROJECT_ROOT / "starseek.db")),
        ephe_path=os.getenv("STARSEEK_EPHE_PATH", str(_PROJECT_ROOT / "data" / "ephe")),
        default_house_system=house_system,
        log_level=os.getenv("STARSEEK_LOG_LEVEL", "INFO"),
        admin_password=os.getenv("STARSEEK_ADMIN_PASSWORD", "admin"),
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings() -> None:
    global _settings
    _settings = None
