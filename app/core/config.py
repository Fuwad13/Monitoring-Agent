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

    # Redis & Celery
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Task Queue Settings
    CELERY_TASK_ALWAYS_EAGER: bool = False  # Set to True for testing
    CELERY_TASK_EAGER_PROPAGATES: bool = False

    # Data Retention
    SNAPSHOT_RETENTION_DAYS: int = 30
    CHANGE_RETENTION_DAYS: int = 90

    # Monitoring Settings
    DEFAULT_MONITORING_FREQUENCY: int = 60  # minutes
    MAX_MONITORING_FREQUENCY: int = 5  # minimum minutes between checks

    # Rate Limiting
    LINKEDIN_REQUESTS_PER_HOUR: int = 50
    WEBSITE_REQUESTS_PER_MINUTE: int = 10
    MAX_CONCURRENT_SCRAPING_TASKS: int = 5

    # Scraping Configuration
    USER_AGENT_ROTATION: bool = True
    REQUEST_DELAY_MIN: int = 1  # seconds
    REQUEST_DELAY_MAX: int = 5  # seconds
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30  # seconds

    # Notification Settings (placeholders for future implementation)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""

    # Security
    ENABLE_RATE_LIMITING: bool = True
    MAX_TARGETS_PER_USER: int = 100

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
