"""Application settings, read from the environment (and backend/.env if present)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "StockSense API"
    API_V1: str = ""

    # SQLite by default so the app runs with no database install; docker-compose
    # sets DATABASE_URL to Postgres.
    DATABASE_URL: str = "sqlite:///./stocksense.db"

    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    OTP_EXPIRE_MINUTES: int = 10
    # Dev convenience: return/print the OTP instead of sending an email.
    DEV_SHOW_OTP: bool = True

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
