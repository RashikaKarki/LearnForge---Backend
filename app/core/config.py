import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


def _read_secret(env_var: str, default: str = "") -> str:
    """Read secret from environment variable or file path (for Cloud Run secrets)"""
    value = os.getenv(env_var, default)

    # If value looks like a file path and exists, read the file
    # This handles Cloud Run's --set-secrets behavior
    if value and os.path.exists(value):
        try:
            with open(value) as f:
                return f.read().strip()
        except Exception:
            return default

    return value


class Settings(BaseSettings):
    APP_TITLE: str = "learnforge-agent-api"
    APP_DESCRIPTION: str = "API for interacting with the Agent learnforge"
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # CORS - loaded from Secret Manager in production
    # Default to localhost only for security - set proper origins in production
    ALLOW_ORIGINS: str = _read_secret(
        "ALLOW_ORIGINS", "http://localhost:3000,http://localhost:8000"
    )

    # Firebase - credentials file path (works for both local and Cloud Run)
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "firebase_key.json"
    )

    # Google API Key - loaded from Secret Manager in production (as file)
    GOOGLE_API_KEY: str = _read_secret("GOOGLE_API_KEY", "")

    YOUTUBE_API_KEY: str = _read_secret("YOUTUBE_API_KEY", "")

    # Database configuration
    DATABASE_URL: str = _read_secret("DATABASE_URL", "")

    # Cloud SQL specific settings (only used in Cloud Run)
    INSTANCE_CONNECTION_NAME: str = _read_secret("INSTANCE_CONNECTION_NAME", "")
    DB_USER: str = _read_secret("DB_USER", "")
    DB_PASSWORD: str = _read_secret("DB_PASSWORD", "")
    DB_NAME: str = _read_secret("DB_NAME", "")

    def __repr__(self):
        """Override __repr__ to prevent logging sensitive information"""
        return f"Settings(APP_TITLE='{self.APP_TITLE}', HOST='{self.HOST}', PORT={self.PORT})"

    # Paths
    AGENTS_DIR: str = "agents"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOW_ORIGINS.split(",")]

    @property
    def is_cloud_run(self) -> bool:
        """Detect if running in Cloud Run environment"""
        return bool(self.INSTANCE_CONNECTION_NAME)

    @property
    def use_cloud_sql_connector(self) -> bool:
        """Determine if Cloud SQL Connector should be used"""
        return self.is_cloud_run and all(
            [self.INSTANCE_CONNECTION_NAME, self.DB_USER, self.DB_PASSWORD, self.DB_NAME]
        )

    class Config:
        case_sensitive = True


settings = Settings()

# CRITICAL: Set GOOGLE_API_KEY in os.environ for google-genai library
# The google-genai library (used by Google ADK) expects the API key in the environment
if settings.GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
