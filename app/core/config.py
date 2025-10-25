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

    # Paths
    AGENTS_DIR: str = "app/agents"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOW_ORIGINS.split(",")]

    class Config:
        case_sensitive = True


settings = Settings()
