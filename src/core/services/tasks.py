from sqlalchemy.orm import Session

from src.core.repositories.tasks import TaskRepository
from src.core.schemas.tasks import TaskRead, TaskBaseResponse
from src.core.utils.uploaded_file import upload_file


class TaskService:
    @staticmethod
    async def create_tasks(
        user_id: int,
        description: str,
        value: int,
        uploaded_file,
        session: Session,
    ):
        photo = await upload_file(uploaded_file)
        new_task = await TaskRepository.create_task(
            user_id,
            description,
            photo,
            value,
            session,
        )
        return TaskRead(status="success", message="Создана новая Задача", task=new_task)

    @staticmethod
    async def update_task(task_id: int, status: str, session: Session):
        msg = await TaskRepository.update_task(task_id, status, session)
        return TaskBaseResponse(status="success", message=msg)

    @staticmethod
    async def delete_task(task_id: int, session: Session):
        msg = await TaskRepository.delete_task(task_id, session)
        return TaskBaseResponse(status="success", message=msg)
