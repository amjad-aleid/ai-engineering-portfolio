import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Read APP_ENV before Settings is instantiated so the right .env file is loaded
_env = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", f".env.{_env}"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = _env
    debug: bool = True
    log_level: str = "DEBUG"

    # API server
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_workers: int = 1
    cors_origins: list[str] = ["*"]

    # LLM
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    # Vector DB
    chroma_db_path: str = "./chroma_db"

    # Retrieval
    retrieval_top_k: int = 10
    rerank_top_k: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
