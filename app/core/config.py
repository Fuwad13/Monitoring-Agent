from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    MONGODB_URI: str

    # Logging
    LOG_FILE_PATH: str = str(Path.cwd() / "app" / "core" / "log" / "app.log")

    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
