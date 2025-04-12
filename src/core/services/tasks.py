import json
import logging
from typing import Optional

from aiohttp import FormData, ClientSession
from fastapi import status, Request, UploadFile, HTTPException
from sqlalchemy.orm import Session

from src.core.jwt.tokens import verify_jwt_token
from src.core.repositories.users import UserRepository
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
        """
        Отправляет задание модератору.

        Возможные входные данные:
        - Только текст
        - Фото + текст
        - Видео + текст
        """
        logger.info(f"Запущена проверка jwt-токена в send_task_to_moderator")
        await verify_user_by_jwt(request=request, session=session)
        logger.info(f"JWT-токен успешно проверен")

        token = request.cookies.get("jwt-token")
        verified_token = verify_jwt_token(token)
        username = verified_token.get("sub")

        answers = {
            1: "https://t.me/c/2621459328/2",
            6: "https://t.me/c/2621459328/4",
            7: "https://t.me/c/2621459328/5",
            8: "https://t.me/c/2621459328/6",
            9: "https://t.me/c/2621459328/7",
            10: "https://t.me/c/2621459328/8",
            11: "https://t.me/c/2621459328/22",
            12: "https://t.me/c/2621459328/9",
            13: "https://t.me/c/2621459328/19",
            14: "https://t.me/c/2621459328/10",
            17: "https://t.me/c/2621459328/11",
            18: "https://t.me/c/2621459328/21",
            19: "https://t.me/c/2621459328/12",
            20: "https://t.me/c/2621459328/13",
            21: "https://t.me/c/2621459328/14",
            25: "https://t.me/c/2621459328/15",
            28: "https://t.me/c/2621459328/20",
            34: "https://t.me/c/2621459328/16",
            35: "https://t.me/c/2621459328/17",
            36: "https://t.me/c/2621459328/18",
        }

        if UserRepository.is_task_already_in_progress(session=session, task_id=task_id, username=username):
            return status.HTTP_200_OK

        logger.info("Создание сообщения")
        if task_id not in answers:
            message = f"📎 Задание №{task_id}\n\n👤 Пользователь: @{username}\n\n💲 Количество баллов: {value}"
        else:
            message = f"📎 Задание №{task_id}\n\n👤 Пользователь: @{username}\n\n💲 Количество баллов: {value}\n\nПроверить ответ: {answers[task_id]}"

        if text and text.strip():
            message += f"\n\n🖋 Текст пользователя: {text}"

        logger.info("Сообщение собрано")

        keyboard = {
            "inline_keyboard": [
                [{"text": "Принять", "callback_data": f"approve_{task_id}_{user_id}_{value}"}],
                [{"text": "Отклонить", "callback_data": f"reject_{task_id}_{user_id}"}]
            ]
        }

        # Определяем, какой тип файла отправлять
        if file:
            # jpeg - норм
            if "image" in file.content_type:
                url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendPhoto"
                file_type = "photo"
            elif "video" in file.content_type:
                url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendVideo"
                file_type = "video"
            else:
                logging.warning(f"Неподдерживаемый формат файла {file.content_type}")
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
        async with ClientSession() as client_session:
            if file:
                async with client_session.post(url, data=form_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to send task to moderator: {error_text}")
                        raise HTTPException(status_code=500, detail=f"Failed to send task to moderator: {error_text}")
            else:
                async with client_session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to send task to moderator: {error_text}")
                        raise HTTPException(status_code=500,
                                            detail=f"Failed to send text task to moderator: {error_text}")

        UserRepository.update_user_in_progress_tasks(session=session, username=username, task_id=task_id)

        return status.HTTP_200_OK
