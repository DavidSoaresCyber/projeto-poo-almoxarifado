from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Moranguinho Stock Manager"
    app_env: str = "development"
    debug: bool = True
    database_url: str = "sqlite:///./moranguinho.db"
    secret_key: str = "moranguinho-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    upload_dir: str = "uploads"
    max_upload_size: int = 5242880
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
