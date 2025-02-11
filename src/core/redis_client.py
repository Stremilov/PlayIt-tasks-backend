import redis

from src.core.utils.config import settings

redis_client = redis.Redis(
    host=settings.redis.REDIS_HOST,
    port=settings.redis.REDIS_PORT,
    db=settings.redis.REDIS_DB,
    decode_responses=True
)

# Это модуль подключения к Redis
