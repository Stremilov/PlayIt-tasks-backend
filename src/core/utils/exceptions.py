import logging
from functools import wraps

from fastapi import HTTPException, status


def handle_http_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            logging.error(f"Exception: {e}")
            raise e
        except Exception as e:
            logging.error(f"Exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Произошла непредвиденная ошибка: {e}",
            )

    return wrapper


NotFoundTasksExcept = HTTPException(
    status_code=404, detail="Задача не найдена в базе данных"
)
NotFoundUsersExcept = HTTPException(
    status_code=404, detail="Пользователь не найден в базе данных"
)
InvalidStatusExcept = HTTPException(status_code=400, detail="Invalid status")
ForbiddenExcept = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав!"
)
UnAuthenticatedExcept = HTTPException(status_code=401, detail="Неавторизован")
