from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sentronix Analytics Service"

    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"

    PORT: int = 8007

    LOG_LEVEL: str = "INFO"

    API_GATEWAY_URL: str = "http://localhost:8000"

    AI_SERVICE_URL: str = "http://localhost:8001"

    CAMERA_SERVICE_URL: str = "http://localhost:8002"

    DEVICE_SERVICE_URL: str = "http://localhost:8003"

    EVENT_SERVICE_URL: str = "http://localhost:8004"

    NOTIFICATION_SERVICE_URL: str = "http://localhost:8005"

    STORAGE_SERVICE_URL: str = "http://localhost:8006"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
