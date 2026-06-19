import copy
import logging
import os
from functools import lru_cache
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.database_config import DatabaseConfig
from app.config.logging_config import LoggingConfig
from app.config.paths import CONTOURS_DIR, ENV_FILE, SETTINGS_DIR

logger = logging.getLogger(__name__)

BASE_CONFIG_PATH = SETTINGS_DIR / "application.yaml"


class RuntimeSettings(BaseSettings):
    """Параметры запуска из окружения."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
    app_profile: str = "sandbox"


class AppConfig(BaseModel):
    """Итоговый конфиг приложения после слияния yaml-файлов."""
    contour: str = "sandbox"
    description: str = ""
    database: DatabaseConfig
    logging: LoggingConfig


def _load_yaml(path: os.PathLike[str] | str) -> dict[str, Any]:
    """Читает yaml-файл в словарь."""
    with open(path, encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config format: {path}")
    return data


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Дополняет общий конфиг значениями из профиля, не затирая соседние поля."""
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _load_merged_config(contour: str) -> dict[str, Any]:
    """Собирает итоговый словарь конфига для профиля."""
    if not BASE_CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Base config not found: {BASE_CONFIG_PATH}")

    contour_path = CONTOURS_DIR / f"{contour}.yaml"
    if not contour_path.is_file():
        available = sorted(path.stem for path in CONTOURS_DIR.glob("*.yaml"))
        raise FileNotFoundError(f"Profile config not found: {contour_path}. Available: {available}")

    merged = _load_yaml(BASE_CONFIG_PATH)
    merged = _deep_merge(merged, _load_yaml(contour_path))
    merged["contour"] = contour
    return merged


@lru_cache
def get_app_config() -> AppConfig:
    """Возвращает типизированный конфиг активного профиля."""
    runtime = RuntimeSettings()
    return AppConfig.model_validate(_load_merged_config(runtime.app_profile))


def log_app_config() -> None:
    """Пишет активный конфиг в лог при старте."""
    config = get_app_config()
    logger.info("Active config (profile=%s, APP_PROFILE=%s):", config.contour, os.getenv("APP_PROFILE", "sandbox"))
    logger.info("%s", yaml.safe_dump(config.model_dump(), allow_unicode=True, sort_keys=False).rstrip())
