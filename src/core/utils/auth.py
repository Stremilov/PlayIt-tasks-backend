from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from src.core.jwt.tokens import verify_jwt_token
from src.core.repositories.users import UserRepository


async def verify_user_by_jwt(request: Request, session: Session):
    """
    Возвращает пользователя после аутентификации по username с помощью jwt
    """
    token = request.cookies.get("jwt-token")
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")

    verified_token = verify_jwt_token(token)

    username_from_jwt = verified_token.get("sub")
    username_from_db = UserRepository.get_user_by_username(session=session, username=username_from_jwt)
    if username_from_db is None or username_from_jwt != username_from_db:
        raise HTTPException(status_code=401, detail="По такому имени в JWT-Токене нет пользователя в базе данных")

