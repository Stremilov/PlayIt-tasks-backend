from typing import Optional
import logging

from fastapi import APIRouter, Request, Form, UploadFile, File, Query, Depends
from sqlalchemy.orm import Session

from src.api.responses import base_bad_response_for_endpoints_of_task, bad_responses_autocheck
from src.core.schemas.tasks import ParseTasksResponse, CheckTaskAnswerInputSchema
from src.core.services.tasks import TaskService
from src.core.services.excel import ExcelService
from src.core.database.db import get_db_session


router = APIRouter()


@router.get(
    path="/get-all",
    response_model=ParseTasksResponse,
    tags=["Tasks"],
    summary="Возвращает возможные задания",
    description="""
    Возвращает все задания из таблицы либо задания по дням с помощью 'day' 

    - Аутентифицирует пользователя по JWT;
    - При первом запросе данные парсятся из Excel и сохраняются в Redis;
    - При последующих запросах данные получаются из кеша.
    - Если day не указан, то вернутся все задания
    - Если day > 3, возвращается ошибка 400.
    """,
)
async def parse_all_tasks(
        request: Request,
        session: Session = Depends(get_db_session),
        day: int | None = Query(
            None,
            description="День, за который нужно получить задания",
        ge=1, # Минимальное значение
        le=3  # Максимальное значение
        )
):
    """
    Эндпоинт для получения всех заданий.
    Сначала пытается вернуть данные из кеша.
    Если кеш пуст или данные невалидны, вызывается ExcelService для парсинга Excel,
    а результат сохраняется в Redis с TTL 6 часов.
    """
    return await TaskService.get_all_tasks(request=request, session=session, day=day)


@router.post(
    path="/create/moderation",
    tags=["Tasks"],
    summary="Создать задание",
    description="Создаёт задание и отправляет его модератору с файлом.",
    responses=base_bad_response_for_endpoints_of_task
)
async def create_task(
        request: Request,
        session: Session = Depends(get_db_session),
        task_id: int = Form(..., description="ID задания"),
        user_id: int = Form(..., description="ID пользователя"),
        value: int = Form(..., description="Количество баллов"),
        text: Optional[str] = Form(default=None, description="Текст выполненного задания"),
        file: Optional[UploadFile] = File(default=None, description="Файл для задания")
):
    """
    Этот эндпоинт принимает данные задания и отправляет его модератору через Telegram Bot API.
    """
    logging.info("Данные приняты")

    if isinstance(file, str) and file == "":
        file = None

    result = await TaskService.send_task_to_moderator(
        request=request,
        session=session,
        task_id=task_id,
        user_id=user_id,
        value=value,
        text=text,
        file=file
    )

    return {"status": result}


@router.post(
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
        request: Request,
        data: CheckTaskAnswerInputSchema,
        session: Session = Depends(get_db_session)
):
    return await ExcelService.check_answer(session=session, request=request, data=data)
