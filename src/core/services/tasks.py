import json
from fastapi import status, Request
from sqlalchemy.orm import Session

from src.core.repositories.tasks import TaskRepository
from src.core.schemas.tasks import TaskRead, TaskBaseResponse
from src.core.utils.uploaded_file import upload_file
from src.core.schemas.tasks import ParseTasksResponse
from src.core.services.excel import ExcelService
from src.core.redis_client import redis_client
from src.core.utils.config import CACHE_KEY, CACHE_EXPIRE


class TaskService:
    @staticmethod
    async def get_all_tasks(request: Request) -> ParseTasksResponse:
        """
        Получает все задания с кешированием:
         1. Пытается получить данные из Redis по ключу 'tasks:all' (Это ключ из .env файла).
         2. Если данные есть и корректны, возвращает их.
         3. Если кеш пуст или данные повреждены, парсит Excel через ExcelService.parse_shop.
         4. Сохраняет полученные данные в Redis с TTL 6 часов (21600 секунд).
        """

        try:
            # Попытка получить данные из кеша
            cached_data = redis_client.get(CACHE_KEY)
        except Exception as redis_error:
            # Если возникла ошибка подключения к Redis – можно залогировать

            cached_data = None

        if cached_data:
            try:
                data = json.loads(cached_data)
                return ParseTasksResponse(
                    status=status.HTTP_200_OK,
                    details="Данные получены из кеша.",
                    data=data,
                )
            except Exception:
                # Если данные в кеше повреждены, удаляем ключ и продолжаем
                redis_client.delete(CACHE_KEY)

        # Если в кеше нет данных или произошла ошибка – вызываем парсер Excel
        response = await ExcelService.parse_shop(request)

        try:
            # Кешируем результат с заданным TTL
            redis_client.set(CACHE_KEY, json.dumps(response.data), ex=CACHE_EXPIRE)
        except Exception:
            # Если ошибка при сохранении в Redis – просто продолжаем без кеша
            pass

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
