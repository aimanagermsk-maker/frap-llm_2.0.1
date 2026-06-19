import json
import logging
from typing import AsyncIterator

import asyncpg

from app.knm_sandbox_delete_after_test_service.knm_json_utils import CustomJSONEncoder

logger = logging.getLogger(__name__)

FETCH_BATCH_SIZE = 500
NDJSON_MEDIA_TYPE = "application/x-ndjson"


def _row_to_ndjson_line(row: dict) -> bytes:
    return (json.dumps(row, cls=CustomJSONEncoder, ensure_ascii=False) + "\n").encode("utf-8")


async def stream_knm_sql(query: str, database_details: dict) -> AsyncIterator[bytes]:
    conn = await asyncpg.connect(
        user=database_details["username"],
        password=database_details["password"],
        host=database_details["host"],
        port=database_details["port"],
        database=database_details["database_name"],
    )
    try:
        async with conn.transaction():
            cursor = conn.cursor(query, prefetch=FETCH_BATCH_SIZE)
            async for record in cursor:
                yield _row_to_ndjson_line(dict(record))
    finally:
        await conn.close()
