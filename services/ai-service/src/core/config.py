from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    AI Service Configuration.
    """

    APP_NAME: str = "Sentronix AI Service"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    DEBUG: bool = True

    # -------------------------
    # YOLO Model
    # -------------------------

    YOLO_MODEL: str = "yolov8n.pt"

    DEVICE: str = "cpu"

    CONFIDENCE_THRESHOLD: float = 0.25

    # -------------------------
    # Detection Filtering
    # -------------------------

    ENABLE_CLASS_FILTER: bool = False

    ALLOWED_CLASSES: list[str] = []

    ENABLE_REGION_FILTER: bool = False

    REGION_X1: int = 0
    REGION_Y1: int = 0
    REGION_X2: int = 0
    REGION_Y2: int = 0

    # -------------------------
    # Tracking
    # -------------------------

    ENABLE_TRACKING: bool = True

    TRACKER_MAX_AGE: int = 30

    # -------------------------
    # Performance
    # -------------------------

    FRAME_SKIP: int = 1

    ENABLE_BATCH_INFERENCE: bool = False

    BATCH_SIZE: int = 4

    # -------------------------
    # Worker Queue
    # -------------------------

    WORKER_ENABLED: bool = True

    QUEUE_MAX_SIZE: int = 100

    # -------------------------
    # Services
    # -------------------------

    API_GATEWAY_URL: str = "http://api-gateway:8000"

    EVENT_SERVICE_URL: str = "http://event-service:8004"

    CAMERA_SERVICE_URL: str = "http://camera-service:8000"

    # -------------------------
    # Storage
    # -------------------------

    SAVE_RESULTS: bool = True

    OUTPUT_DIR: str = "outputs"

    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
