import logging

import pymssql
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

DB_TYPE_MSSQL = 'MSSQL'


def _execute_sql_mssql_sync(
        query: str,
        database_details: dict,
        params: list | tuple | None = None,
):
    """Выполняет синхронно SQL в MySQL"""
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

        if params is None:
            cur.execute(query)
        else:
            # В pymssql плейсхолдеры – %s
            # Пример запроса: "SELECT * FROM clients WHERE owner_id = %s"
            cur.execute(query, params)

        return cur.fetchall()
        # Если будут проблемы с типами данных, то преобразуем в обычный dict
        # return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


async def execute_sql_mssql(
        query: str,
        database_details: dict,
        params: list | tuple | None = None,
):
    """Async-обёртка для FastAPI – вызывает sync-функцию в threadpool."""
    try:
        return await run_in_threadpool(
            _execute_sql_mssql_sync,
            query,
            database_details,
            params,
        )
    except Exception as e:
        logger.error(f"Error executing MSSQL SQL query: {query}, params={params}, error: {e!r}")
        raise HTTPException(status_code=400, detail=str(e))
