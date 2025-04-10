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

    @staticmethod
    def update_user_in_progress_tasks(session: Session, username: str, task_id: int):
        stmt = text("""
                UPDATE users
                SET in_progress = array_append(COALESCE(in_progress, '{}'), :task_id)
                WHERE username = :username
            """)
        session.execute(stmt, {"task_id": task_id, "username": username})
        session.commit()

    @staticmethod
    def is_task_already_in_progress(session: Session, username: str, task_id: int) -> bool:
        stmt = text("""
            SELECT :task_id = ANY(in_progress)
            FROM users
            WHERE username = :username
        """)
        result = session.execute(stmt, {"task_id": task_id, "username": username}).scalar()
        return bool(result)


