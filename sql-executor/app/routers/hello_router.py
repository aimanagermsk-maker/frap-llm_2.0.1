from fastapi import APIRouter

router = APIRouter(
    tags=["Test"]
)


@router.get(
    "/hello",
    summary="Проверка доступности сервиса",
    description="Возвращает тестовое сообщение. Авторизация не требуется.",
)
def hello():
    return {"text": "Ура, работает!"}
