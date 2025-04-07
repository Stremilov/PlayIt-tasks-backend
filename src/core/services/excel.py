import json
import logging

from fastapi import HTTPException, status, Request
from pandas import read_excel, DataFrame
from sqlalchemy.orm import Session

from src.core.schemas.tasks import (
    CheckTaskAnswerInputSchema,
    CheckTaskAnswerOutputSchema,
    UpdateUserBalanceData
)
from src.core.services.aiohttp_client import AiohtppClientService
from src.core.utils.auth import verify_user_by_jwt

logger = logging.getLogger("excel_logger")

class ExcelService:
    @staticmethod
    async def _parse_excel(columns_to_drop: list, max_day: int | None) -> DataFrame:
        file_path = "PlayIT.xlsx"

        # Проверка, что файл имеет корректное расширение
        if not file_path.endswith(".xlsx" or ".xls"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unprocessable content",
            )

        # Чтение Excel-файла с данными листа 'Персонажи'
        excel_shop_df = read_excel(file_path, sheet_name="Персонажи")
        if excel_shop_df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Таблицы 'Персонажи' не существует.",
            )

        if max_day is not None: # Проверка передали ли день?
            if "Номер дня" not in excel_shop_df.columns:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="В таблице не существует колонки 'Номер дня'."
                )

            excel_shop_df = excel_shop_df[excel_shop_df["Номер дня"] <= max_day] # Фильтруем до максимального дня

        if columns_to_drop: # Если есть колонки для удаления, то удаляем их
            excel_shop_df = excel_shop_df.drop(columns=[col for col in columns_to_drop if col in excel_shop_df.columns])
        return excel_shop_df

    @staticmethod
    async def parse_table(request: Request, day: int | None) -> DataFrame:
        """
        Парсит Excel-файл и возвращает данные в виде DataFrame.
        """
        # user = await verify_user_by_jwt(request)
        # if not user:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        # file_path = os.path.join("data", "PlayIT")

        excel_shop_df = await ExcelService._parse_excel(columns_to_drop=["Ответ", "Аватарка"], max_day=day)
        return excel_shop_df

    @staticmethod
    async def check_answer(
            request: Request,
            session: Session,
            data: CheckTaskAnswerInputSchema
    ) -> CheckTaskAnswerOutputSchema:
        """
        Проверяет, совпадает ли ответ пользователя с правильным ответом из Excel-файла.
         - True, если ответ совпал;
         - False, если ответ не совпал;
        Затем, если ответ правильный, то отправляет запрос с помощью aiohttp на ручку пополнения баланса.
        """
        logger.info(f"Запущена проверка jwt-токена в get_all_tasks")
        await verify_user_by_jwt(request=request, session=session)
        logger.info(f"JWT-токен успешно проверен")

        # TODO: закэшировать
        try:
            excel_shop_df = await ExcelService._parse_excel(columns_to_drop=["Аватарка"], max_day=None)

            row = excel_shop_df[excel_shop_df["№"] == data.task_id]
            if row.empty:
                raise HTTPException(status_code=404, detail="Задание не найдено")

            correct_answer = str(row.iloc[0]["Ответ"]).strip().lower()
            result = correct_answer == data.user_answer.strip().lower()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{str(e)}")

        if result:
            # Если ответ правильный, формируем данные для обновления баланса.
            balance_data = UpdateUserBalanceData(
                task_id=data.task_id,
                user_id=data.user_id,
                value=data.value,
                status="approved",
                tg=True
            )
            await AiohtppClientService.update_user_balance(balance_data, request)

        return CheckTaskAnswerOutputSchema(
            task_id=data.task_id,
            is_correct=result
        )

