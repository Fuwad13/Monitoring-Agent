from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOG_FILE_PATH: str = str(Path.cwd() / "app" / "log" / "app.log")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
