import json
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Request, Form, UploadFile, File, Query

from src.api.responses import base_bad_response_for_endpoints_of_task, bad_responses_autocheck
from src.core.schemas.tasks import ParseTasksResponse, CheckTaskAnswerInputSchema
from src.core.services.tasks import TaskService
from src.core.services.excel import ExcelService

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
    path="/create/moderation",
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

    result = await TaskService.send_task_to_moderator(task_id, user_id, value, text, file)

    return {"status": result}


# TODO: Оставить ли Put или всё же Get, но без пайдентик схемы?
# Переделал с Get на Put, потому что в Get запросе нельзя запрашивать pydantic схему, а в тудушке было
# перейти на пд схему
@router.put(
    path="/create/autocheck",
    tags=["Tasks"],
    summary="Проверить ответ на задание",
    description=
    "Проверяет, правильно ли пользователь ответил на задание, "
    "для проверки используется Excel-файл 'PlayIT.xlsx' (лист 'Персонажи'),"
    "где в колонке '№' хранится ID задания, а в колонке 'Ответ' — правильный ответ.",
    responses=bad_responses_autocheck
)
async def check_task_answer(
        payload: CheckTaskAnswerInputSchema
):
    task_id = payload.task_id
    user_answer = payload.user_answer
    result = ExcelService.check_answer(task_id, user_answer)

    return {
        "task_id": task_id,
        "is_correct": result
    }
