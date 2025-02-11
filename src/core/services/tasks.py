import json
import logging

from fastapi import status, Request

from src.core.utils.config import settings
from src.core.schemas.tasks import ParseTasksResponse
from src.core.services.excel import ExcelService
from src.core.redis_client import redis_client

logger = logging.getLogger("tasks_logger")



class TaskService:

    # @staticmethod
    # def _send_task_to_moderator(user_id: int, value: int, photo: UploadFile):
    #     url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendPhoto"
    #     message = (f"Новое задание от пользователя:\n\n"
    #                f"Количество баллов: {value}")
    #
    #     keyboard = {
    #         "inline_keyboard": [
    #             [{"text": "Принять", "callback_data": f"approve_{user_id}_{value}"}],
    #             [{"text": "Отклонить", "callback_data": f"reject_{user_id}"}]
    #         ]
    #     }
    #
    #     files = {}
    #     if photo:
    #         files = {'photo': (photo.filename, photo.file, photo.content_type)}
    #
    #     data = {
    #         "chat_id": settings.bot.MODERATOR_CHAT_ID,
    #         "caption": message,
    #         "reply_markup": json.dumps(keyboard)
    #     }
    #
    #     try:
    #         requests.post(url, data=data, files=files if photo else None)
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=str(e))
    #
    #     return status.HTTP_200_OK

    @staticmethod
    def _get_cached_data():
        try:
            logger.debug("Попытка получить данные из Redis по ключу '%s'", settings.redis.CACHE_KEY)
            data = redis_client.get(settings.redis.CACHE_KEY)
            logger.debug("Данные из Redis успешно получены.")
            return data
        except Exception as e:
            logger.error("Ошибка при получении данных из Redis по ключу '%s': %s", settings.redis.CACHE_KEY, e,
                         exc_info=True)
            return None

    @staticmethod
    def _parse_cached_data(cached_data):
        try:
            parsed = json.loads(cached_data)
            logger.debug("Десериализация данных из кеша прошла успешно.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error("Ошибка десериализации данных из кеша: %s", e, exc_info=True)
            try:
                redis_client.delete(settings.redis.CACHE_KEY)
                logger.debug("Поврежденный ключ '%s' удален из Redis", settings.redis.CACHE_KEY)
            except Exception as delete_error:
                logger.error("Ошибка удаления поврежденного ключа '%s': %s", settings.redis.CACHE_KEY, delete_error,
                             exc_info=True)
            return None

    @staticmethod
    def _cache_response(response: ParseTasksResponse):
        try:
            serialized = json.dumps(response.data)
            redis_client.set(settings.redis.CACHE_KEY, serialized, ex=settings.redis.CACHE_EXPIRE)
            logger.debug("Данные успешно сохранены в Redis по ключу '%s' с TTL %s секунд.", settings.redis.CACHE_KEY,
                         settings.redis.CACHE_EXPIRE)
        except Exception as e:
            logger.error("Ошибка при сохранении данных в Redis по ключу '%s': %s", settings.redis.CACHE_KEY, e,
                         exc_info=True)

    @staticmethod
    async def get_all_tasks(request: Request) -> ParseTasksResponse:
        """
        Получает все задания с кешированием:
         1. Пытается получить данные из Redis по ключу 'tasks:all'.
         2. Если данные есть и корректны, возвращает их.
         3. Если кеш пуст или данные повреждены, парсит Excel через ExcelService.parse_shop.
         4. Сохраняет полученные данные в Redis с TTL 6 часов (21600 секунд).
        """
        logger.info("Запущен метод get_all_tasks()")
        cached_data = TaskService._get_cached_data()

        if cached_data:
            parsed_data = TaskService._parse_cached_data(cached_data)
            if parsed_data:
                logger.info("Данные получены из кеша и успешно десериализованы.")
                return ParseTasksResponse(
                    status=status.HTTP_200_OK,
                    details="Данные получены из кеша.",
                    data=parsed_data,
                )
            else:
                logger.info("Кешированные данные повреждены. Переходим к парсингу Excel.")

        logger.info("Парсинг Excel-файла через ExcelService.parse_shop()")
        response = await ExcelService.parse_shop(request)
        logger.info("Данные успешно получены через ExcelService.")

        TaskService._cache_response(response)
        logger.info("Метод get_all_tasks() завершён. Данные возвращены клиенту.")

        return response

    # @staticmethod
    # async def create_tasks(
    #         user_id: int,
    #         description: str,
    #         value: int,
    #         uploaded_file,
    #         session: Session,
    # ):
    #     result = TaskService._send_task_to_moderator(user_id=user_id, value=value, photo=uploaded_file)
    #     if result == status.HTTP_200_OK:
    #         return TaskBaseResponse(status="200", message="success")
