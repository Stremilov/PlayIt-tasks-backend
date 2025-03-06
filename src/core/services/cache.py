import json
import logging

from src.core.utils.config import settings
from src.core.redis_client import redis_client
from src.core.schemas.tasks import ParseTasksResponse

logger = logging.getLogger("cache_logger")

class CacheService:
    @staticmethod
    def get_cached_data():
        try:
            logger.debug("Попытка получить данные из Redis по ключу '%s'", settings.redis.CACHE_KEY)
            data = redis_client.get(settings.redis.CACHE_KEY)
            logger.debug("Данные из Redis успешно получены.")
            return data
        except Exception as e:
            logger.error("Ошибка при получении данных из Redis по ключу '%s': %s", settings.redis.CACHE_KEY, e,
                         exc_info=True)
            return None


    @staticmethod
    def parse_cached_data(cached_data):
        try:
            parsed = json.loads(cached_data)
            logger.debug("Десериализация данных из кеша прошла успешно.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error("Ошибка десериализации данных из кеша: %s", e, exc_info=True)
            try:
                redis_client.delete(settings.redis.CACHE_KEY)
                logger.debug("Поврежденный ключ '%s' удален из Redis", settings.redis.CACHE_KEY)
            except Exception as delete_error:
                logger.error("Ошибка удаления поврежденного ключа '%s': %s", settings.redis.CACHE_KEY, delete_error,
                             exc_info=True)
            return None


    @staticmethod
    def cache_response(response: ParseTasksResponse):
        try:
            serialized = json.dumps(response.data)
            redis_client.set(settings.redis.CACHE_KEY, serialized, ex=settings.redis.CACHE_EXPIRE)
            logger.debug("Данные успешно сохранены в Redis по ключу '%s' с TTL %s секунд.", settings.redis.CACHE_KEY,
                         settings.redis.CACHE_EXPIRE)
        except Exception as e:
            logger.error("Ошибка при сохранении данных в Redis по ключу '%s': %s", settings.redis.CACHE_KEY, e,
                         exc_info=True)
