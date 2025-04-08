import json
import logging
import tempfile
from typing import Optional
from PIL import Image

from aiohttp import FormData, ClientSession
from fastapi import status, Request, UploadFile, HTTPException
from sqlalchemy.orm import Session

from src.core.utils.config import settings
from src.core.schemas.tasks import ParseTasksResponse
from src.core.services.excel import ExcelService
from src.core.services.cache import CacheService
from src.core.utils.auth import verify_user_by_jwt

logger = logging.getLogger("tasks_logger")


class TaskService:
    @staticmethod
    async def get_all_tasks(
            request: Request,
            session: Session,
            day: int | None = None) -> ParseTasksResponse:
        logger.info(f"Запущен метод get_all_tasks(), day={day}")

        logger.info(f"Запущена проверка jwt-токена в get_all_tasks")
        await verify_user_by_jwt(request=request, session=session)
        logger.info(f"JWT-токен успешно проверен")

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
            request: Request,
            session: Session,
            task_id: int,
            user_id: int,
            value: int,
            text: Optional[str] = None,
            file: Optional[UploadFile] = None
    ):
        logger.info(f"Запущена проверка jwt-токена в send_task_to_moderator")
        await verify_user_by_jwt(request=request, session=session)
        logger.info(f"JWT-токен успешно проверен")

        message = f"Новое задание от пользователя:\n\nКоличество баллов: {value}"
        if text:
            message += f"\n\nТекст пользователя: {text}"

        keyboard = {
            "inline_keyboard": [
                [{"text": "Принять", "callback_data": f"approve_{task_id}_{user_id}_{value}"}],
                [{"text": "Отклонить", "callback_data": f"reject_{task_id}_{user_id}"}]
            ]
        }

        if file:
            content_type = file.content_type
            file_type = None
            url = None

            # Конвертация изображений в PNG, если необходимо
            if "image" in content_type:
                image = Image.open(file.file)
                image.thumbnail((1600, 1600), Image.ANTIALIAS)
                temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                image.save(temp_file, format="PNG", optimize=True)
                temp_file.seek(0)
                file_to_send = temp_file
                file_type = "photo"
                url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendPhoto"
            elif "video" in content_type:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.write(await file.read())
                temp_file.seek(0)
                file_to_send = temp_file
                file_type = "video"
                url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendVideo"
            else:
                logger.warning(f"Неподдерживаемый формат файла {content_type}")
                raise HTTPException(status_code=400, detail="Неподдерживаемый формат файла")

            temp_file.seek(0, 2)
            size_in_mb = temp_file.tell() / 1024 / 1024
            temp_file.seek(0)

            if size_in_mb > 10 and file_type == "photo":
                raise HTTPException(status_code=413, detail="Файл изображения слишком большой (максимум 10MB)")

            form_data = FormData()
            form_data.add_field('chat_id', str(settings.bot.MODERATOR_CHAT_ID))
            form_data.add_field('caption', message)
            form_data.add_field('reply_markup', json.dumps(keyboard))
            form_data.add_field(file_type, file_to_send,
                                filename="converted.png" if file_type == "photo" else file.filename,
                                content_type="image/png" if file_type == "photo" else content_type)

        else:
            url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": str(settings.bot.MODERATOR_CHAT_ID),
                "text": message,
                "reply_markup": json.dumps(keyboard),
                "parse_mode": "HTML",
            }

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
