import aiohttp
import logging

from fastapi import HTTPException
from src.core.schemas.tasks import UpdateUserBalanceData
from src.core.utils.config import BASE_URL_FOR_AIOHTTP

logger = logging.getLogger("aiohttp_logger")

class AiohtppClientService:
    @staticmethod
    async def send_patch_request(endpoint: str, payload: dict) -> dict:
        """
        Отправляет PATCH-запрос по указанному эндпоинту с заданным пейлоадом
        """
        logger.debug("Заход в метод send_patch_request")
        url = f"{BASE_URL_FOR_AIOHTTP}/{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                logger.debug("Заход в контекстный менеджер отправки PATCH запроса в методе send_patch_request")
                async with session.patch(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise HTTPException(status_code=response.status, detail=error_text)
                    logger.debug("PATCH запрос успешно отправлен успешно в методе send_patch_request")
                    return await response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Непредвиденная ошибка при отправке PATCH-запроса на: '{url}'")

    @staticmethod
    async def update_user_balance(data: UpdateUserBalanceData) -> dict:
        logger.debug("Заход в метод update_user_balance")
        endpoint = "users/balance"
        payload = data.model_dump()
        return await AiohtppClientService.send_patch_request(endpoint, payload)