from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AeroInsight API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/database.db"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "aero_literature"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"  # Full GPT-4o for better reasoning (upgraded from mini)

    # RAG retrieval
    RETRIEVAL_TOP_K: int = 10


# Singleton — import this everywhere instead of re-instantiating
settings = Settings()
