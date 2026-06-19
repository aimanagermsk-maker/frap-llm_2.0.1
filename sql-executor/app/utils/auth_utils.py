"""
Проверка JWT из заголовка Authorization (как в SQL Agent).

Подпись не проверяется (verify_signature=False)
"""

import logging
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

logger = logging.getLogger(__name__)

# Используется в Depends(...) — в Swagger появляется кнопка Authorize
security = HTTPBearer()

def decode_jwt(credentials: HTTPAuthorizationCredentials) -> dict:
    """Декодирует JWT из Bearer-токена без проверки подписи."""
    try:
        payload = jwt.decode(credentials.credentials, options={"verify_signature": False})
    except Exception as e:
        logger.error("Invalid token %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid token {e}")
    return payload

def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI-зависимость: полный payload JWT."""
    return decode_jwt(credentials)


def get_token_payload_metalens_org_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """ FastAPI-зависимость: Ожидается единственная metalens_org_id из JWT. """
    payload = decode_jwt(credentials)
    org_id = payload.get("metalens_org_id")
    logger.info("metalens_org_id=%s", org_id)
    if not org_id or len(org_id) > 1:
        logger.error("Exactly one organization required: metalens_org_id=%s", org_id)
        raise HTTPException(status_code=400, detail=f"Должна быть указана одна организация metalens_org_id={org_id}")
    return org_id[0]

def get_token_payload_given_name(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """FastAPI-зависимость: поле given_name из JWT."""
    payload = decode_jwt(credentials)
    given_name = payload.get("given_name")
    logger.info("given_name=%s", given_name)
    return given_name
