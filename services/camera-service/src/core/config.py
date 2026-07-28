from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sentronix Camera Service"

    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"

    PORT: int = 8002

    LOG_LEVEL: str = "INFO"

    UPLOAD_DIR: str = "uploads"

    RECORDING_DIR: str = "recordings"

    MAX_CAMERA_COUNT: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
