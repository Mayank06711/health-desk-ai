from pydantic_settings import BaseSettings
from openai import AsyncOpenAI


class Settings(BaseSettings):
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

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/voice_agent"

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"

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
