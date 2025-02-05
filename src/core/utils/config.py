import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Для создания БД
DB_PASSWORD = os.getenv("DATABASE_PASSWORD")
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_KEY = os.getenv("CACHE_KEY", "tasks:all")  # Ключ для хранения данных кеша
CACHE_EXPIRE = int(os.getenv("CACHE_EXPIRE", 21600))  # Время жизни кеша: 6 часов = 6 * 3600 секунд

UPLOAD_FOLDER = Path("uploads/images")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
