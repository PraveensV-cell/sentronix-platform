from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """
    Device Service Configuration
    """

    APP_NAME: str = "Sentronix Device Service"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8003

    LOG_LEVEL: str = "INFO"

    API_GATEWAY_URL: str = "http://localhost:8000"

    HEARTBEAT_INTERVAL: int = 10

    DEVICE_ID: str = "DEVICE-001"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
