from fastapi_users.jwt import decode_jwt
from fastapi import HTTPException
from src.core.utils.config import settings


def verify_jwt_token(token: str) -> dict:
    """
    Синхронно декодирует и проверяет JWT-токен.
    """
    try:
        audience = "prod"  # Должно совпадать с "aud" в create_jwt_token
        return decode_jwt(token, settings.token.SECRET_KEY, audience)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Невалидный токен: {str(e)}")
