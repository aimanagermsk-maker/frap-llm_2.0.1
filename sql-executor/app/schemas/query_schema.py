from pydantic import BaseModel, Field


class ExecuteQueryRequest(BaseModel):
    """Тело запроса на потоковое выполнение SQL."""

    database: int = Field(
        ...,
        description="id записи в chat_settings_databases",
        examples=[123],
    )
    sql: str = Field(
        ...,
        min_length=1,
        description="SQL-запрос для выполнения на целевой БД",
        examples=["SELECT id, name FROM users LIMIT 1000"],
    )
