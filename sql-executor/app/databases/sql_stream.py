"""
Потоковое выполнение SQL: строки отдаются по одной (NDJSON), без накопления всего результата в памяти.
"""
import asyncio
import json
import logging
import threading
from typing import AsyncIterator

import aiomysql
import asyncpg
import pymssql
import vertica_python

from app.databases.universal_mssql_database import DB_TYPE_MSSQL
from app.databases.universal_mysql_database import DB_TYPE_MYSQL, DB_TYPE_MARIADB
from app.databases.universal_pg_database import DB_TYPE_POSTGRES
from app.databases.universal_vertica_database import DB_TYPE_VERTICA
from app.utils.json_utils import CustomJSONEncoder

logger = logging.getLogger(__name__)

FETCH_BATCH_SIZE = 500
NDJSON_MEDIA_TYPE = "application/x-ndjson"


def _row_to_ndjson_line(row: dict) -> bytes:
    """Преобразует строку результата в NDJSON-байты."""
    return (json.dumps(row, cls=CustomJSONEncoder, ensure_ascii=False) + "\n").encode("utf-8")


async def stream_sql(query: str, database_details: dict) -> AsyncIterator[bytes]:
    """Потоково выполняет SQL и отдаёт строки в NDJSON."""
    database_type = database_details.get("database_type")
    if database_type == DB_TYPE_POSTGRES:
        async for chunk in _stream_sql_pg(query, database_details):
            yield chunk
    elif database_type == DB_TYPE_MSSQL:
        async for chunk in _stream_sql_sync_driver(query, database_details, _produce_mssql):
            yield chunk
    elif database_type in (DB_TYPE_MYSQL, DB_TYPE_MARIADB):
        async for chunk in _stream_sql_mysql(query, database_details):
            yield chunk
    elif database_type == DB_TYPE_VERTICA:
        async for chunk in _stream_sql_sync_driver(query, database_details, _produce_vertica):
            yield chunk
    else:
        raise ValueError(f"База данных ({database_type}) не поддерживается")


async def _stream_sql_pg(query: str, database_details: dict) -> AsyncIterator[bytes]:
    """Потоково выполняет SQL в PostgreSQL и отдаёт строки в NDJSON."""
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


async def _stream_sql_mysql(query: str, database_details: dict) -> AsyncIterator[bytes]:
    """Потоково выполняет SQL в MySQL/MariaDB и отдаёт строки в NDJSON."""
    conn = await aiomysql.connect(
        user=database_details["username"],
        password=database_details["password"],
        host=database_details["host"],
        port=database_details["port"],
        db=database_details["database_name"],
        charset="utf8mb4",
    )
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(query)
            while True:
                rows = await cursor.fetchmany(FETCH_BATCH_SIZE)
                if not rows:
                    break
                for row in rows:
                    yield _row_to_ndjson_line(row)
    finally:
        conn.close()


async def _stream_sql_sync_driver(
        query: str,
        database_details: dict,
        producer,
) -> AsyncIterator[bytes]:
    """Потоково выполняет SQL через синхронный драйвер в отдельном потоке и отдаёт строки в NDJSON."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[bytes | None | Exception] = asyncio.Queue(maxsize=64)

    def run_producer():
        """Вызывает producer(метод - который читает строки из БД) в отдельном потоке (выполняет SQL и кладёт NDJSON-строки в очередь)."""
        try:
            producer(query, database_details, queue, loop)
        except Exception as exc:
            loop.call_soon_threadsafe(queue.put_nowait, exc)
            loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=run_producer, daemon=True).start()

    while True:
        item = await queue.get()
        if item is None:
            break
        if isinstance(item, Exception):
            raise item
        yield item


def _produce_mssql(query: str, database_details: dict, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Читает строки из MSSQL и кладёт их в очередь как NDJSON."""
    conn = pymssql.connect(
        server=database_details["host"],
        port=database_details["port"],
        user=database_details["username"],
        password=database_details["password"],
        database=database_details["database_name"],
        login_timeout=5,
        timeout=30,
        as_dict=True,
    )
    try:
        cur = conn.cursor()
        cur.execute(query)
        while True:
            rows = cur.fetchmany(FETCH_BATCH_SIZE)
            if not rows:
                break
            for row in rows:
                loop.call_soon_threadsafe(queue.put_nowait, _row_to_ndjson_line(row))
    finally:
        conn.close()
        loop.call_soon_threadsafe(queue.put_nowait, None)


def _produce_vertica(query: str, database_details: dict, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Читает строки из Vertica и кладёт их в очередь как NDJSON."""
    conn = vertica_python.connect(
        user=database_details["username"],
        password=database_details["password"],
        host=database_details["host"],
        port=database_details["port"],
        database=database_details["database_name"],
        connection_timeout=300,
        tlsmode="disable",
    )
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        while True:
            rows = cursor.fetchmany(FETCH_BATCH_SIZE)
            if not rows:
                break
            for row in rows:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    _row_to_ndjson_line(dict(zip(columns, row))),
                )
    finally:
        cursor.close()
        conn.close()
        loop.call_soon_threadsafe(queue.put_nowait, None)
