from pydantic import BaseModel, Field


class SystemAppToken(BaseModel):
    """Токен системного приложения с именем из заголовка ===...===."""
    app: str = Field(..., description="Имя приложения (из ===App=== или метка для запасного)")
    token: str = Field(..., description="JWT")
