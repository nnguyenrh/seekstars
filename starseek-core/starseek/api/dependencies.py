from functools import lru_cache

from starseek.config import Settings, load_settings
from starseek.services.storage import init_db


@lru_cache
def get_settings() -> Settings:
    return load_settings()


def get_db_path() -> str:
    settings = get_settings()
    init_db(settings.db_path, admin_password=settings.admin_password)
    return settings.db_path
