from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class UserRepository:
    @staticmethod
    def get_user_by_username(session: Session, username: str) -> Optional[str]:
        stmt = text("""
                select username
                from users
                where username = :username
                """)
        result = session.execute(stmt, {"username": username})
        row = result.fetchone()

        return row[0] if row else None


