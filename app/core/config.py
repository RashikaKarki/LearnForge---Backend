import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    APP_TITLE: str = "learnforge-agent-api"
    APP_DESCRIPTION: str = "API for interacting with the Agent learnforge"
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # CORS - loaded from Secret Manager in production
    ALLOW_ORIGINS: str = os.getenv("ALLOW_ORIGINS", "*")

    # Firebase - credentials loaded from Secret Manager in production
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "firebase_key.json"
    )

    # Google API Key - loaded from Secret Manager in production
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Paths
    AGENTS_DIR: str = "app/agents"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOW_ORIGINS.split(",")]

    class Config:
        case_sensitive = True


settings = Settings()
