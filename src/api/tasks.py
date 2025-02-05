from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from sqlalchemy.orm import Session

from src.api.responses import base_bad_response_for_endpoints_of_task
from src.core.database.db import get_db_session
from src.core.schemas.tasks import ParseTasksResponse, TaskRead, TaskBaseResponse
from src.core.services.excel import ExcelService
from src.core.services.tasks import TaskService

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
    "/create",
    response_model=TaskRead,
    tags=["Tasks"],
    status_code=201,
    summary="Создание новой задачи",
    description="""
                Эндпоинт для создания задачи. Сохраняет фото в локальной папке и записывает задачу в базу данных.
                """,
    responses=base_bad_response_for_endpoints_of_task,
)
async def create_task(
    user_id: int = Form(...),
    description: str = Form(...),
    value: int = Form(...),
    uploaded_file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
):
    return await TaskService.create_tasks(
        user_id=user_id,
        description=description,
        value=value,
        uploaded_file=uploaded_file,
        session=session
    )


# @router.patch(
#     "/{task_id}",
#     response_model=TaskBaseResponse,
#     tags=["Tasks"],
#     summary="Обновления статуса задачи по id",
#     responses=base_bad_response_for_endpoints_of_task,
# )
# async def update_task_status(
#     task_id: int,
#     status: str,
#     session: Session = Depends(get_db_session),
# ):
#     return await TaskService.update_task(task_id, status, session)


@router.delete(
    "/{task_id}",
    response_model=TaskBaseResponse,
    tags=["Tasks"],
    summary="Удаление задачи по id",
    responses=base_bad_response_for_endpoints_of_task,
)
async def delete_task(task_id: int, session: Session = Depends(get_db_session)):
    return await TaskService.delete_task(task_id, session)
