import logging
import re
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from app.config.paths import ENV_FILE
from app.schemas.dev_auth_schema import SystemAppToken

logger = logging.getLogger(__name__)

_SECTION_HEADER_RE = re.compile(r"^===([^=]+)===$", re.MULTILINE)


def format_tokens_for_log(tokens: list[SystemAppToken]) -> str:
    """Форматирует список токенов для вывода в лог."""
    if not tokens:
        return "  (empty)"
    result_tokens_lines: list[str] = []
    for index, entry in enumerate(tokens, start=1):
        result_tokens_lines.append(f"  [{index}] ==={entry.app}===")
        result_tokens_lines.append(f"      {entry.token}")
    return "\n".join(result_tokens_lines)


def _parse_system_apps_tokens(system_apps_token_env: Any) -> list[SystemAppToken]:
    """
    Парсит токены из формата ===App=== JWT ===App=== JWT
    в формат: list[app: "App", token: "JWT"]
    """
    if not isinstance(system_apps_token_env, str):
        return []

    trimmed_tokens_env = system_apps_token_env.strip()
    if not trimmed_tokens_env or "===" not in trimmed_tokens_env:
        return []

    parsed_tokens: list[SystemAppToken] = []
    split_tokens = _SECTION_HEADER_RE.split(trimmed_tokens_env)
    for index in range(1, len(split_tokens), 2):
        app_name = split_tokens[index].strip()
        jwt_token = (split_tokens[index + 1] if index + 1 < len(split_tokens) else "").strip()
        if not app_name or not jwt_token:
            continue
        parsed_tokens.append(SystemAppToken(app=app_name, token=jwt_token))
    return parsed_tokens


class SystemAppsSettings(BaseSettings):
    """Токены для доступа к API."""
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    system_apps_tokens: Annotated[list[SystemAppToken], NoDecode] = Field(
        default_factory=list,
        validation_alias="SYSTEM_APPS_TOKEN",
    )

    @field_validator("system_apps_tokens", mode="before")
    @classmethod
    def parse_system_apps_tokens(cls, system_apps_token_env_value: Any) -> list[SystemAppToken]:
        """Валидатор pydantic: преобразует строку из env в список токенов."""
        return _parse_system_apps_tokens(system_apps_token_env_value)


system_apps_settings = SystemAppsSettings()


def log_system_apps_tokens_state() -> None:
    """Логирует токены из SYSTEM_APPS_TOKEN при старте приложения."""
    loaded_system_app_tokens = system_apps_settings.system_apps_tokens
    logger.info("system_apps_tokens: count=%s %s", len(loaded_system_app_tokens), format_tokens_for_log(loaded_system_app_tokens))
