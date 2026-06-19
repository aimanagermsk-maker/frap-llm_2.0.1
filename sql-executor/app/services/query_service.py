import logging
from typing import AsyncIterator

from fastapi import HTTPException

from app.databases.analytics_ai_database import get_database_details
from app.databases.sql_stream import NDJSON_MEDIA_TYPE, stream_sql
from app.schemas.query_schema import ExecuteQueryRequest

logger = logging.getLogger(__name__)


async def resolve_database_details(database_id: int) -> dict:
    """Загружает параметры подключения к целевой БД из analytics-ai по id БД из chat_settings_databases."""
    try:
        details = await get_database_details(str(database_id))
    except IndexError:
        raise HTTPException(status_code=404, detail=f"Database with id = {database_id} not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load database with id = {database_id} connection settings") from exc

    if not details or not details.get("host"):
        raise HTTPException(status_code=404, detail=f"Database with id = {database_id} not found")

    # подменяем адрес БД
    hosts_to_change = {
        "127.0.0.1":  "postgres",  #todo удалить после решения https://tracker.yandex.ru/MLP-121
    }
    original_host = details["host"]
    if original_host in hosts_to_change:
        details = {**details, "host": hosts_to_change[original_host]}
        logger.info("DB host remapped: %s -> %s", original_host, details["host"])

    return details


async def execute_query_stream(request: ExecuteQueryRequest) -> tuple[AsyncIterator[bytes], str]:
    """По database_id загружает настройки БД и выполняет SQL с потоковой отдачей результата."""
    database_details = await resolve_database_details(request.database)
    sql = request.sql.strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL query is empty")

    logger.info("Executing SQL: database_id=%s type=%s sql=%s", request.database, database_details.get("database_type"), sql)

    try:
        row_stream = stream_sql(sql, database_details)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Ошибка при выполнении SQL: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return row_stream, NDJSON_MEDIA_TYPE
