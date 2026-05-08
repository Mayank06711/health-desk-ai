from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LiveKit
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Deepgram
    DEEPGRAM_API_KEY: str = ""

    # Cartesia
    CARTESIA_API_KEY: str = ""

    # Simli (optional — avatar added in Layer 7)
    SIMLI_API_KEY: str = ""
    SIMLI_FACE_ID: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/voice_agent"

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    FRONTEND_URL: str = "http://localhost:3000"

    # Cartesia voice
    CARTESIA_VOICE_ID: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
