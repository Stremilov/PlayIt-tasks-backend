import json
import logging
from typing import Optional

from aiohttp import ClientSession, FormData
from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from starlette import status

from src.api.responses import base_bad_response_for_endpoints_of_task
from src.core.schemas.tasks import ParseTasksResponse
from src.core.services.tasks import TaskService
from src.core.utils.config import settings

router = APIRouter()


@router.get(
    path="/get-all",
    response_model=ParseTasksResponse,
    tags=["Tasks"],
    summary="Возвращает все возможные задания",
    description="""
    Возвращает все задания из таблицы

    - Аутентифицирует пользоватея по JWT;
    - При первом запросе данные парсятся из Excel и сохраняются в Redis;
    - При последующих запросах данные получаются из кеша.
    """,
)
async def parse_all_tasks(request: Request):
    """
    Эндпоинт для получения всех заданий.
    Сначала пытается вернуть данные из кеша.
    Если кеш пуст или данные невалидны, вызывается ExcelService для парсинга Excel,
    а результат сохраняется в Redis с TTL 6 часов.
    """
    return await TaskService.get_all_tasks(request)


@router.post(
    path="/create",
    tags=["Tasks"],
    summary="Создать задание",
    description="Создаёт задание и отправляет его модератору с файлом.",
    responses=base_bad_response_for_endpoints_of_task
)
async def create_task(
        task_id: int = Form(..., description="ID задания"),
        user_id: int = Form(..., description="ID пользователя"),
        value: str = Form(..., description="Количество баллов"),
        text: Optional[str] = Form(default=None, description="Текст выполненного задания"),
        file: Optional[UploadFile] = File(default=None, description="Файл для задания")
):
    """
    Этот эндпоинт принимает данные задания и отправляет его модератору через Telegram Bot API.
    """
    logging.info("Данные приняты")

    if isinstance(file, str) and file == "":
        file = None

    # Передаем параметры в правильном порядке
    result = await send_task_to_moderator(task_id, user_id, value, text, file)

    return {"status": result}


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
                    raise HTTPException(status_code=500, detail=f"Failed to send text task to moderator: {error_text}")

    return status.HTTP_200_OK
