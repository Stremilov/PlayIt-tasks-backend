from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class UserRepository:
    @staticmethod
    def get_user_by_username(session: Session, username: str) -> Optional[tuple]:
        stmt = text("""
            SELECT *
            from users
            where username = :username
            """)

        result = session.execute(stmt, {"username": username})
        # Достаём теперь не кортеж, а именно int - число коинов пользователя
        user = result.scalar_one_or_none()
        if not user:
            return None

        return user # Возвращаем первый элемент кортежа (balance) или 0, если пользователь не найден