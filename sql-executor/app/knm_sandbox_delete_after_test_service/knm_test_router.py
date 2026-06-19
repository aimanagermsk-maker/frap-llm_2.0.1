from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.knm_sandbox_delete_after_test_service.knm_schema import KnmSqlRequest
from app.knm_sandbox_delete_after_test_service import knm_service
from app.utils.auth_utils import get_token_payload_metalens_org_id

router = APIRouter(
    prefix="/query",
    tags=["Авторизованный доступ. Выполнить SQL в KNM sandbox"],
)


@router.get(
    "/execute/test/knm",
    summary="Выполнить SQL в песочной БД КНМ и получить данные",
    responses={403: {"description": "Отсутствует или неверный заголовок Authorization"}},
)
async def knm_test_execute(
    request: KnmSqlRequest,
    org_id: str = Depends(get_token_payload_metalens_org_id),
):
    row_stream, media_type = await knm_service.execute_knm_request_stream(request)
    return StreamingResponse(
        row_stream,
        media_type=media_type,
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )
