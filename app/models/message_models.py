python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class IncomingMessage(BaseModel):
    """Структура входящего сообщения из Kafka"""
    id: str = Field(..., description="Идентификатор запроса")
    type: str = Field(..., description="Тип запроса (например, frapclaims)")
    date: date = Field(..., description="Дата в формате YYYY-MM-DD")
    uri: str = Field(..., description="Имя файла в формате UUID")
    
    def get_file_path(self, base_path: str) -> str:
        """Формирует путь к файлу: {base_path}/{date}/{type}/{uri}"""
        return f"{base_path}/{self.date}/{self.type}/{self.uri}"
