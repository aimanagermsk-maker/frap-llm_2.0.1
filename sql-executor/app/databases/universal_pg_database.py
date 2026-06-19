import logging

import asyncpg
from fastapi import HTTPException

logger = logging.getLogger(__name__)

DB_TYPE_POSTGRES = 'PostgreSQL'


async def execute_sql_pg(query: str, database_details: dict):
    """Выполняет SQL в PostgreSQL. асинхронно"""
    try:
        conn = await asyncpg.connect(user=database_details['username'], password=database_details['password'],
                                     host=database_details['host'], port=database_details['port'],
                                     database=database_details['database_name'])
        rows = await conn.fetch(query)
        await conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error executing PostgreSQL SQL query: {query}, error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
