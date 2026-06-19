from pydantic import BaseModel, Field


class KnmSqlRequest(BaseModel):
    sql: str = Field(..., min_length=1, description="SQL-запрос к песочной БД КНМ")
