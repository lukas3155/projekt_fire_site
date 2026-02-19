from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    SECRET_KEY: str = "change-me-to-random-64-char-string"
    SITE_URL: str = "http://localhost:8000"
    SITE_NAME: str = "Projekt FIRE"

    DATABASE_URL: str = "postgresql+asyncpg://fire:fire@db:5432/projektfire"

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me"

    CONTACT_EMAIL: str = "kontakt@projektfire.pl"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
