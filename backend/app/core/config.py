from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS: int = 384
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.6-flash"

    LLM_PROVIDER: str = "gemini"
    OLLAMA_MODEL: str = "llama3.1"


settings = Settings()