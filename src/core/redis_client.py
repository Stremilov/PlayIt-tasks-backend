import redis
from src.core.utils.config import REDIS_HOST, REDIS_PORT, REDIS_DB

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True  # Получаем строки, а не байты
)

# Это модуль подключения к Redis
