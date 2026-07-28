from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sentronix Storage Service"

    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"

    PORT: int = 8006

    LOG_LEVEL: str = "INFO"

    STORAGE_DIR: str = "storage"

    IMAGE_DIR: str = "storage/images"

    VIDEO_DIR: str = "storage/videos"

    SNAPSHOT_DIR: str = "storage/snapshots"

    TEMP_DIR: str = "storage/temp"

    MAX_FILE_SIZE: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
