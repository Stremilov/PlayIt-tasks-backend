import json
from fastapi import status, Request
from sqlalchemy.orm import Session

from src.core.repositories.tasks import TaskRepository
from src.core.schemas.tasks import TaskRead, TaskBaseResponse
from src.core.utils.config import settings
from src.core.utils.uploaded_file import upload_file
from src.core.schemas.tasks import ParseTasksResponse
from src.core.services.excel import ExcelService
from src.core.redis_client import redis_client


class TaskService:

    @staticmethod
    def _get_cached_data():
        try:
            return redis_client.get(settings.redis.CACHE_KEY)
        except Exception as e:
            # Логирование ошибки подключения к Redis
            return None

    @staticmethod
    def _parse_cached_data(cached_data):
        try:
            return json.loads(cached_data)
        except json.JSONDecodeError:
            redis_client.delete(settings.redis.CACHE_KEY)
            return None

    @staticmethod
    def _cache_response(response):
        try:
            redis_client.set(settings.redis.CACHE_KEY, json.dumps(response.data), ex=settings.redis.CACHE_KEY)
        except Exception:
            # Ошибка при сохранении в Redis – логирование по необходимости
            pass

    @staticmethod
    async def get_all_tasks(request: Request) -> ParseTasksResponse:
        """
        Получает все задания с кешированием:
          1. Пытается получить данные из Redis по ключу 'tasks:all'.
          2. Если данные есть и корректны, возвращает их.
          3. Если кеш пуст или данные повреждены, парсит Excel через ExcelService.parse_shop.
          4. Сохраняет полученные данные в Redis с TTL 6 часов (21600 секунд).
        """
        cached_data = TaskService._get_cached_data()

        if cached_data:
            parsed_data = TaskService._parse_cached_data(cached_data)
            if parsed_data:
                return ParseTasksResponse(
                    status=status.HTTP_200_OK,
                    details="Данные получены из кеша.",
                    data=parsed_data,
                )

        response = await ExcelService.parse_shop(request)
        TaskService._cache_response(response)

        return response

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
    # async def update_task(task_id: int, status: str, session: Session):
    #     msg = await TaskRepository.update_task(task_id, status, session)
    #     return TaskBaseResponse(status="success", message=msg)

    @staticmethod
    async def delete_task(task_id: int, session: Session):
        msg = await TaskRepository.delete_task(task_id, session)
        return TaskBaseResponse(status="success", message=msg)
