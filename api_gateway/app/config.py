from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Настройки приложения
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # URL других сервисов
    file_service_url: str
    analysis_service_url: str

    # Настройки обработки ошибок
    timeout_seconds: int = 30

    class Config:
        env_file = ".env"


settings = Settings()