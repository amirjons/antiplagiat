from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Настройки приложения
    app_host: str = "0.0.0.0"
    app_port: int = 8001

    # База данных
    database_url: str

    # Файлы
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    allowed_extensions: List[str] = ["txt", "pdf", "doc", "docx"]

    class Config:
        env_file = ".env"


settings = Settings()