import logging

import asyncpg
from fastapi import HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.paths import ENV_FILE

logger = logging.getLogger(__name__)


class _AnalyticsAiDbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
    db_config_pg_dashboard: str


DB_CONFIG_PG_DASHBOARD = _AnalyticsAiDbSettings().db_config_pg_dashboard


async def execute_sql_analytics_ai(query: str, params: list | tuple = None):
    """Выполняет SQL в БД analytics-ai (PostgreSQL) и возвращает строки как список dict."""
    try:
        conn = await asyncpg.connect(DB_CONFIG_PG_DASHBOARD)
        try:
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
        finally:
            await conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error executing PostgreSQL SQL query: {query}, error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


async def get_database_details(chat_settings_database_id: str):
    """Возвращает полную информацию для подключения и метаданные БД по id БД из chat_settings_databases."""
    database_details_sql = """
                           SELECT instructions, ddl_schema,
                                  title, db_type AS database_type, host, port, db_name AS database_name, username, password
                              FROM chat_settings_databases csd LEFT JOIN meta_database md ON csd.database_id = md.id
                              WHERE csd.id = $1
                           """
    database_details_params_sql = [int(chat_settings_database_id)]
    database_details_list = await execute_sql_analytics_ai(database_details_sql, database_details_params_sql)
    return database_details_list[0]
