from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sentronix Event Service"
    APP_VERSION: str = "1.0.0"

    HOST: str = "0.0.0.0"
    PORT: int = 8004

    LOG_LEVEL: str = "INFO"

    API_GATEWAY_URL: str = "http://localhost:8000"

    CAMERA_SERVICE_URL: str = "http://camera-service:8002"

    DEVICE_SERVICE_URL: str = "http://device-service:8003"

    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"

    STORAGE_SERVICE_URL: str = "http://storage-service:8006"

    ANALYTICS_SERVICE_URL: str = "http://analytics-service:8007"

    DATABASE_HOST: str = "postgres"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "sentronix"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@postgres:5432/sentronix"
    )

    REDIS_URL: str = "redis://redis:6379"

    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/"

    EVENT_RETENTION_DAYS: int = 30
    EVENT_BATCH_SIZE: int = 100
    MAX_EVENT_QUEUE_SIZE: int = 10000
    EVENT_PROCESSING_THREADS: int = 4

    ENABLE_HEALTH_CHECK: bool = True
    HEALTH_CHECK_INTERVAL: int = 30

    REQUEST_TIMEOUT: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
