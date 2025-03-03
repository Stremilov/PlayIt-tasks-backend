import json
from fastapi import HTTPException, status, Request
from pandas import read_excel, DataFrame
from src.core.schemas.tasks import (
    CheckTaskAnswerInputSchema,
    CheckTaskAnswerOutputSchema
)


class ExcelService:
    @staticmethod
    async def parse_table(request: Request) -> DataFrame:
        """
        Парсит Excel-файл и возвращает данные в виде DataFrame.
        """
        # user = await verify_user_by_jwt(request)
        # if not user:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        # file_path = os.path.join("data", "PlayIT")

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

        return excel_shop_df

    @staticmethod
    async def check_answer(
            request: Request,
            data: CheckTaskAnswerInputSchema
    ) -> CheckTaskAnswerOutputSchema:
        """
        Проверяет, совпадает ли ответ пользователя с правильным ответом из Excel-файла.
        Возвращает:
         - True, если ответ совпал;
         - False, если ответ не совпал;
        """
        # TODO: Закешировать
        df = await ExcelService.parse_table(Request)

        row = df[df["№"] == data.task_id]
        if row.empty:
            raise HTTPException(status_code=404, detail="Задание не найдено")
        correct_answer = str(row.iloc[0]["Ответ"]).strip().lower()
        result = correct_answer == data.user_answer.strip().lower()

        # TODO если ответ правильный, то сделать запрос с помощью aiohttp на ручку
        #  it-otdel.space/playit/auth/users/balance с patch запросом

        # Если нужна документация, то она находтся по адресу it-otdel.space/playit/auth/docs

        # Структура входных данных ниже
        # Если ответ пользователя правильный, то status передать "approved"

        # class UpdateUserBalanceData(BaseModel):
        #     task_id: int
        #     user_id: int
        #     value: int
        #     status: str

        return CheckTaskAnswerOutputSchema(
            task_id=data.task_id,
            is_correct=result
        )
