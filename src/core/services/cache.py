import json
import logging

from src.core.utils.config import settings
from src.core.redis_client import redis_client
from src.core.schemas.tasks import ParseTasksResponse

logger = logging.getLogger("cache_logger")


class CacheService:
    @staticmethod
    def get_day_data(day: int):
        """Получает данные для конкретного дня из кеша"""
        cache_key = settings.redis.CACHE_KEY_TEMPLATE.format(day=day)
        try:
            data = redis_client.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении данных дня {day} из Redis: {e}", exc_info=True)
            return None

    @staticmethod
    def cache_day_data(day: int, data: dict):
        """Кеширует данные для конкретного дня"""
        cache_key = settings.redis.CACHE_KEY_TEMPLATE.format(day=day)
        try:
            redis_client.set(cache_key, json.dumps(data), ex=settings.redis.CACHE_EXPIRE)
            logger.debug(f"Данные дня {day} успешно сохранены в Redis")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных дня {day} в Redis: {e}", exc_info=True)

    @staticmethod
    def get_all_cached_days():
        """Получает все доступные дни из кеша"""
        try:
            # Получаем все ключи, соответствующие шаблону
            keys = redis_client.keys(settings.redis.CACHE_KEY_TEMPLATE.format(day="*"))
            days = []
            for key in keys:
                # Извлекаем номер дня из ключа
                day = int(key.split(":")[-1])
                days.append(day)
            return sorted(days)
        except Exception as e:
            logger.error(f"Ошибка при получении списка дней из кеша: {e}", exc_info=True)
            return []

    @staticmethod
    def get_accumulated_data(day: int | None = None):
        """
        Получает накопленные данные:
        - если day=None - все данные из кеша
        - если указан day - данные за все дни до day включительно
        """
        result = []
        if day is None:
            # Получаем все доступные дни
            days = CacheService.get_all_cached_days()
        else:
            # Получаем дни от 1 до указанного
            days = range(1, day + 1)

        # TODO: Тут можно сделать поумнее, если какой-то день отсутствует, но другие есть в кеше, то спарсить именно его
        # TODO: С excel таблички, а остальные достать из кеша
        for day_num in days:
            day_data = CacheService.get_day_data(day_num)
            if day_data:
                result.extend(day_data)
            else:
                return None  # Если какой-то день отсутствует

        return result if result else None
