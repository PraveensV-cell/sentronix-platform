from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    ENVIRONMENT: str

    HOST: str
    PORT: int

    DEBUG: bool

    API_PREFIX: str
    API_DESCRIPTION: str

    CONTACT_NAME: str
    CONTACT_EMAIL: str

    LICENSE_NAME: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_URL: str

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM: str

    ADMIN_EMAIL: str

    AI_SERVICE_URL: str = "http://ai-service:8001"

    EVENT_SERVICE_URL: str = "http://event-service:8004"

    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8005"

    STORAGE_SERVICE_URL: str = "http://storage-service:8006"

    ANALYTICS_SERVICE_URL: str = "http://analytics-service:8007"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
