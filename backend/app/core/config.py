from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Immo"

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000", "http://localhost:3001"]

    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/immo"

    # AI Model Configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY")
    print(f"Loaded ANTHROPIC_API_KEY from environment: {'Yes' if ANTHROPIC_API_KEY else 'No'}")
    if ANTHROPIC_API_KEY:
        print(f"API key starts with: {ANTHROPIC_API_KEY[:10]}...")
    DEFAULT_MODEL: str = "claude-3-sonnet"
    MAX_CHAPTERS: int = 10

    # Environment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
