from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    MONGODB_URI: str

    # Logging
    LOG_FILE_PATH: str = str(Path.cwd() / "app" / "core" / "log" / "app.log")

    CHROME_DRIVER_PATH: str = str(Path.cwd() / "app" / "chromedriver.exe")

    # LinkedIn
    LNKDIN_EMAIL: str
    LNKDIN_PASSWORD: str

    # AI/LLM Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.1

    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str = "Monitoring Agent"

    LNKDIN_COOKIES_PATH: str = str(Path.cwd() / "lnkdin_cookies.txt")

    REDIS_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
