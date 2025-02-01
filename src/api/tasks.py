from fastapi import APIRouter, Request

from src.schemas.tasks import ParseTasksResponse
from src.services.excel import ExcelService

router = APIRouter()


@router.get(
    path="/get-all",
    response_model=ParseTasksResponse,
    summary="Возвращает все возможные задания",
    description="""
    Возвращает все задания из таблицы

    - Аутентифицирует пользоватея по JWT;
    - Парсит excel таблицу;
    - Возвращает все задания.
    """
)
async def parse_all_tasks(request: Request):
    return await ExcelService.parse_shop(request)
