from fastapi import APIRouter, Request

from src.schemas.tasks import ParseTasksResponse
from src.services.excel import ExcelService

router = APIRouter()


@router.get(
    path="/get-all",
    response_model=ParseTasksResponse
)
async def parse_all_tasks(request: Request):
    return await ExcelService.parse_shop(request)
