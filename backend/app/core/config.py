from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Immo"

    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://localhost:3000"]

    #AI Model Configuration
    ANTHROPIC_API_KEY: str
    DEFAULT_MODEL: str = "claude-3-sonnet"
    MAX_CHAPTERS: int = 10

    # Enviornment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True


    class Config:
        env_file =".env"

settings = Settings()