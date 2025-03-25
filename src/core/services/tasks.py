import json
import logging
from typing import Optional

from aiohttp import FormData, ClientSession
from fastapi import status, Request, UploadFile, HTTPException

from src.core.utils.config import settings
from src.core.schemas.tasks import ParseTasksResponse
from src.core.services.excel import ExcelService
from src.core.services.cache import CacheService

logger = logging.getLogger("tasks_logger")


class TaskService:
    @staticmethod
    async def get_all_tasks(request: Request, day: int | None = None) -> ParseTasksResponse:
        logger.info(f"Запущен метод get_all_tasks(), day={day}")

        # Пытаемся получить данные из кеша
        cached_data = CacheService.get_accumulated_data(day)

        if cached_data is not None:
            logger.info(f"Данные {'за все дни' if day is None else f'за дни 1-{day}'} получены из кеша.")
            return ParseTasksResponse(
                status=status.HTTP_200_OK,
                details=f"Данные {'за все дни' if day is None else f'за дни 1-{day}'} получены из кеша.",
                data=cached_data,
            )

        # Если в кеше нет данных, парсим Excel
        logger.info(f"Парсинг Excel-файла через ExcelService.parse_table(day={day})")
        excel_shop_df = await ExcelService.parse_table(request, day)

        # Преобразуем в JSON
        json_data = excel_shop_df.to_json(orient="records")
        formatted_json_data = json.loads(json_data)

        if not formatted_json_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка при форматировании данных из таблицы",
            )

        # Разделяем данные по дням и кешируем каждый день отдельно
        if 'Номер дня' in excel_shop_df.columns:
            for day_num in range(1, 4): # От 1 до 3 дней
                day_data = excel_shop_df[excel_shop_df['Номер дня'] == day_num]
                day_json = day_data.to_json(orient="records")
                CacheService.cache_day_data(day_num, json.loads(day_json))


        response = ParseTasksResponse(
            status=status.HTTP_200_OK,
            details="Данные успешно получены из Excel файла.",
            data=formatted_json_data,
        )

        logger.info("Метод get_all_tasks() завершён. Данные возвращены клиенту.")
        return response

    @staticmethod
    async def send_task_to_moderator(
            task_id: int, user_id: int, value: str, text: Optional[str] = None, file: Optional[UploadFile] = None
    ):
        """
        Отправляет задание модератору.

        Возможные входные данные:
        - Только текст
        - Фото + текст
        - Видео + текст
        """

        message = f"Новое задание от пользователя:\n\nКоличество баллов: {value}"
        if text:
            message += f"\n\nТекст пользователя: {text}"

        keyboard = {
            "inline_keyboard": [
                [{"text": "Принять", "callback_data": f"approve_{task_id}_{user_id}_{value}"}],
                [{"text": "Отклонить", "callback_data": f"reject_{task_id}_{user_id}"}]
            ]
        }

        # Определяем, какой тип файла отправлять
        if file:
            if "image" in file.content_type:
                url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendPhoto"
                file_type = "photo"
            elif "video" in file.content_type:
                url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendVideo"
                file_type = "video"
            else:
                raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла")

            # Формируем данные для отправки
            form_data = FormData()
            form_data.add_field('chat_id', str(settings.bot.MODERATOR_CHAT_ID))
            form_data.add_field('caption', message)  # Описание (подпись)
            form_data.add_field('reply_markup', json.dumps(keyboard))
            form_data.add_field(file_type, file.file, filename=file.filename, content_type=file.content_type)

        else:
            # Если файл отсутствует, отправляем только текст
            url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendMessage"

            payload = {
                "chat_id": str(settings.bot.MODERATOR_CHAT_ID),
                "text": message,
                "reply_markup": json.dumps(keyboard),
                "parse_mode": "HTML",
            }

        # Отправка запроса
        async with ClientSession() as session:
            if file:
                async with session.post(url, data=form_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=500, detail=f"Failed to send task to moderator: {error_text}")
            else:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=500,
                                            detail=f"Failed to send text task to moderator: {error_text}")

        return status.HTTP_200_OK
