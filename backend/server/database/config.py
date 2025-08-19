import os
from typing import Optional

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://user:password@localhost:5432/dbname"
    )
    echo_sql: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    pool_pre_ping: bool = True
    pool_recycle: int = 3600  # 1 hour

    class Config:
        env_file = ".env"


settings = DatabaseSettings()