import json
import logging

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
    summary="Создать задание",
    description="Создаёт задание и отправляет его модератору с фото.",
    responses=base_bad_response_for_endpoints_of_task
)
async def create_task(
    task_id: int = Form(..., description="ID задания"),
    user_id: int = Form(..., description="ID пользователя"),
    value: str = Form(..., description="Количество баллов"),
    photo: UploadFile = File(..., description="Фото для задания")
):
    """
    Этот эндпоинт принимает данные задания и отправляет его модератору через Telegram Bot API.
    """
    logging.info("Данные приняты")
    result = await send_task_to_moderator(task_id, user_id, value, photo)
    return {"status": result}


async def send_task_to_moderator(task_id: int, user_id: int, value: str, photo: UploadFile):
    url = f"https://api.telegram.org/bot{settings.bot.TELEGRAM_BOT_TOKEN}/sendPhoto"

    message = (f"Новое задание от пользователя:\n\n"
               f"Количество баллов: {value}")

    keyboard = {
        "inline_keyboard": [
            [{"text": "Принять", "callback_data": f"approve_{task_id}_{user_id}_{value}"}],
            [{"text": "Отклонить", "callback_data": f"reject_{task_id}_{user_id}"}]
        ]
    }

    form_data = FormData()
    form_data.add_field('chat_id', str(settings.bot.MODERATOR_CHAT_ID))
    form_data.add_field('caption', message)
    form_data.add_field('reply_markup', json.dumps(keyboard))
    form_data.add_field('photo', photo.file, filename=photo.filename, content_type=photo.content_type)

    async with ClientSession() as session:
        async with session.post(url, data=form_data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise HTTPException(status_code=500, detail=f"Failed to send task to moderator: {error_text}")

    return status.HTTP_200_OK
