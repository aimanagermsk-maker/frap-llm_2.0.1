import os
from contextlib import asynccontextmanager

import logging
import uvicorn
import yaml

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.config.logging_config import LOGGING_CONFIG
from app.config.system_apps_config import log_system_apps_tokens_state
from app.routers import query_router, hello_router
from app.knm_sandbox_delete_after_test_service import knm_test_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_system_apps_tokens_state()
    yield


VERSION = "1.0"
API_ROOT_PATH = os.getenv("API_ROOT_PATH", "")

app = FastAPI(
    title="Database API",
    description="Потоковое выполнение SQL по id базы из analytics-ai.",
    version=VERSION,
    root_path=API_ROOT_PATH,
    servers=[
        {"url": "/gateway/api/database-api", "description": "Production"},
        {"url": "/", "description": "Local"},
    ],
    docs_url="/docs",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

logger = logging.getLogger(__name__)
logger.info("Starting Database API version: %s", VERSION)


@app.exception_handler(HTTPException)
async def log_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Логирует HTTPException и возвращает стандартный JSON-ответ FastAPI с полем detail."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    message = f"HTTP {exc.status_code} {request.method} {request.url.path}: {detail}"
    if exc.status_code >= 500:
        if exc.__cause__:
            logger.error("%s: %s", message, exc.__cause__)
        else:
            logger.error(message)
    else:
        logger.warning(message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers,
    )

    security_schemes = schema.get("components", {}).get("securitySchemes", {})
    for scheme in security_schemes.values():
        if scheme.get("type") == "http" and scheme.get("scheme") == "bearer":
            scheme["description"] = "JWT"

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _custom_openapi


@app.get("/openapi.yaml", include_in_schema=False)
def openapi_yaml():
    """Возвращает сгенерированную схему OpenAPI в YAML (аналог `/docs`, без UI)."""
    return Response(
        yaml.safe_dump(
            app.openapi(),
            sort_keys=False,
            allow_unicode=True,
        ),
        media_type="application/yaml",
    )


app.include_router(hello_router.router)
app.include_router(query_router.router)
app.include_router(knm_test_router.router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9010,
        reload=True,
        log_config=LOGGING_CONFIG,
    )
