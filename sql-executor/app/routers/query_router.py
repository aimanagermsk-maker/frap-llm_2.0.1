from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas.query_schema import ExecuteQueryRequest
from app.services import query_service
from app.utils.auth_utils import get_token_payload_metalens_org_id

router = APIRouter(
    prefix="/query",
    tags=["Авторизованный доступ. Выполнить SQL  "],
)


@router.get(
    "/execute",
    summary="Выполнить SQL в переданной БД (по id) и получить данные",
    description="Выполняет SQL в БД, выбирая её по id в analytics-ai.",
    responses={
        200: {
            "description": "Поток строк результата в формате NDJSON",
            "content": {
                "application/x-ndjson": {
                    "example": '{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}',
                }
            },
        },
        400: {"description": "Некорректный JWT, пустой SQL, неподдерживаемая СУБД или ошибка выполнения запроса", },
        403: {"description": "Отсутствует или неверный заголовок Authorization"},
        404: {"description": "База данных с указанным database_id не найдена"},
    },
)
async def execute_query(
    request: ExecuteQueryRequest,
    org_id: str = Depends(get_token_payload_metalens_org_id), #todo возможно в этом сервисе не нужно проверять организацию из jwt
):
    row_stream, media_type = await query_service.execute_query_stream(request)
    return StreamingResponse(
        row_stream,
        media_type=media_type,
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )
