import os
from dotenv import load_dotenv

load_dotenv()

# Для создания БД
DB_PASSWORD = os.getenv("DATABASE_PASSWORD")
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PORT = os.getenv("DATABASE_PORT", "5432")

SECRET_KEY = os.getenv("SECRET_KEY")  # Секретный ключ для подписи JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Время жизни токена в минутах (Сутки)

# Получаем URL базы данных из переменной окружения или используем значение по умолчанию (это нужно, чтобы в тестах можно
# было легко и удобно использовать другую базу данных)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)