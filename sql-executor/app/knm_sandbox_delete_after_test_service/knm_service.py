import logging
from typing import AsyncIterator

from fastapi import HTTPException

from app.knm_sandbox_delete_after_test_service.knm_config import KNM_DATABASE_DETAILS
from app.knm_sandbox_delete_after_test_service.knm_schema import KnmSqlRequest
from app.knm_sandbox_delete_after_test_service.knm_sql_stream import NDJSON_MEDIA_TYPE, stream_knm_sql

logger = logging.getLogger(__name__)


async def execute_knm_sql_stream(sql: str) -> tuple[AsyncIterator[bytes], str]:
    query = sql.strip()
    if not query:
        raise HTTPException(status_code=400, detail="SQL query is empty")

    logger.info("KNM sandbox SQL: %s", query[:200])

    try:
        row_stream = stream_knm_sql(query, KNM_DATABASE_DETAILS)
    except Exception as exc:
        logger.error("KNM sandbox SQL error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return row_stream, NDJSON_MEDIA_TYPE


async def execute_knm_request_stream(request: KnmSqlRequest) -> tuple[AsyncIterator[bytes], str]:
    return await execute_knm_sql_stream(request.sql)
