from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sentronix AI Service"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    DEBUG: bool = True

    YOLO_MODEL: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.25
    DEVICE: str = "cpu"

    API_GATEWAY_URL: str = "http://api-gateway:8000"
    EVENT_SERVICE_URL: str = "http://event-service:8004"

    SAVE_RESULTS: bool = True
    OUTPUT_DIR: str = "outputs"

    # Ignore additional variables present in the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
