from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update
from typing import Optional

from src.models.models import Users
from src.schemas.users import UserSchema, UpdatePersonalDataSchema


class UserRepository:
    @staticmethod
    def create_user(session: Session, data: dict) -> UserSchema:
        statement = insert(Users).values(**data).returning(Users)
        result = session.execute(statement)
        session.commit()

        created_user = result.scalars().first()
        new_user = created_user.to_read_model()
        return new_user

    @staticmethod
    def get_user_by_username(session: Session, username: str) -> Optional[UserSchema]:
        statement = select(Users).filter_by(username=username)
        result = session.execute(statement)

        user = result.scalar_one_or_none()
        if not user:
            return None
        return user.to_read_model()

    @staticmethod
    def update_user_balance(session: Session, username: str, value: int):
        statement = update(Users).where(Users.username == username).values(balance=Users.balance + value)
        session.execute(statement)
        session.commit()

        statement = select(Users).filter_by(username=username)
        result = session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return None
        return user.to_read_model()

    @staticmethod
    def update_user_personal_data(session: Session, username: str, new_data: UpdatePersonalDataSchema):
        update_values = {}

        if new_data.full_name is not None and new_data.full_name != "":
            update_values['full_name'] = new_data.full_name

        if new_data.group_number is not None and new_data.group_number != "":
            update_values['group_number'] = new_data.group_number

        statement = update(Users).where(Users.username == username).values(**update_values)
        session.execute(statement)
        session.commit()

        statement = select(Users).filter_by(username=username)
        result = session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return None
        return user.to_read_model()