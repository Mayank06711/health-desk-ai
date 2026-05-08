from pydantic_settings import BaseSettings
from openai import AsyncOpenAI


class Settings(BaseSettings):
    # Runtime flag — determines which internal URLs to use
    RUNNING_IN_DOCKER: bool = False

    # LiveKit
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    # LLM — single config, used everywhere
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "google/gemini-2.0-flash-001"

    # Deepgram
    DEEPGRAM_API_KEY: str = ""

    # Cartesia
    CARTESIA_API_KEY: str = ""
    CARTESIA_VOICE_ID: str = ""

    # Simli (optional)
    SIMLI_API_KEY: str = ""
    SIMLI_FACE_ID: str = ""

    # Database — raw values, config derives the actual URL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "voice_agent"

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def DATABASE_URL(self) -> str:
        if self.RUNNING_IN_DOCKER:
            # Inside Docker: postgres is the container name, port 5432 (internal)
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgres:5432/{self.POSTGRES_DB}"
        # Local dev: postgres on host, mapped to port 5433
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:5433/{self.POSTGRES_DB}"

    @property
    def FRONTEND_URL(self) -> str:
        if self.RUNNING_IN_DOCKER:
            return "http://frontend:80"
        return "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


def get_async_llm_client() -> AsyncOpenAI:
    """Single factory for async LLM client. Every service uses this."""
    return AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )
