import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic.v1 import BaseSettings

load_dotenv()

UPLOAD_FOLDER = Path("uploads/images")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
)

BASE_URL_FOR_AIOHTTP = "https://it-otdel.space/playit/auth" # Адрес, куда будут лететь запросы

class LoggingSettings(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "debug"

    log_format: str = LOG_DEFAULT_FORMAT

    @property
    def log_level_value(self) -> int:
        return logging.getLevelNamesMapping()[self.log_level.upper()]


class RunSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8001


class BotSettings(BaseModel):
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    MODERATOR_CHAT_ID: str = os.getenv("MODERATOR_CHAT_ID")


class DBSettings(BaseModel):
    DB_PASSWORD: str = os.getenv("DATABASE_PASSWORD")
    DB_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DB_NAME: str = os.getenv("DATABASE_NAME", "postgres")
    DB_USER: str = os.getenv("DATABASE_USER", "postgres")
    DB_PORT: str = os.getenv("DATABASE_PORT", "5432")
    DATABASE_URL: str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class TokenSettings(BaseModel):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24


class RedisSettings(BaseModel):
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    CACHE_KEY_TEMPLATE: str = os.getenv("CACHE_KEY_TEMPLATE", "tasks:day:{day}")  # Ключ для хранения данных кеша для дня
    CACHE_EXPIRE: int = int(os.getenv("CACHE_EXPIRE", 21600))  # Время жизни кеша: 6 часов = 6 * 3600 секунд


class Settings(BaseSettings):
    bot: BotSettings = BotSettings()
    db: DBSettings = DBSettings()
    token: TokenSettings = TokenSettings()
    redis: RedisSettings = RedisSettings()
    logging: LoggingSettings = LoggingSettings()
    run: RunSettings = RunSettings()


settings = Settings()