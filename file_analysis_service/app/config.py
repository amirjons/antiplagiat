from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Настройки приложения
    app_host: str = "0.0.0.0"
    app_port: int = 8002

    # База данных
    database_url: str = "sqlite:///./analysis.db"

    # Другие сервисы
    file_service_url: str

    # Настройки анализа
    quickchart_url: str = "https://quickchart.io"

    class Config:
        env_file = ".env"


settings = Settings()