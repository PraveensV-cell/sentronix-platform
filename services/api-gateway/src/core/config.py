from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SENTRONIX API Gateway"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    API_PREFIX: str = "/api/v1"

    API_DESCRIPTION: str = (
        "Enterprise AI Surveillance Platform built using "
        "FastAPI Microservices Architecture."
    )

    CONTACT_NAME: str = "Shidigonde Praveen"
    CONTACT_EMAIL: str = "shidigondePraveenshetty@gmail.com"

    LICENSE_NAME: str = "MIT"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int


settings = Settings()
