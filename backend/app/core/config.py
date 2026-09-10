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

    # Bounds worst-case per-call cost regardless of prompt quality — see
    # backend/COST_OPTIMIZATION.md.
    LLM_MAX_OUTPUT_TOKENS: int = 500

    # --- Auth ---
    # No default: a signing key that falls back to a hard-coded value is a
    # signing key that ships to production. Missing it fails startup loudly.
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Email-verification and password-reset tokens are signed with a
    # DIFFERENT secret from session tokens. If one leaks, it must not be
    # usable to mint the other - a verification link is emailed in
    # plaintext and passes through mail servers, so it lives in a much
    # less trusted place than a session cookie.
    EMAIL_TOKEN_SECRET: str
    EMAIL_TOKEN_EXPIRE_MINUTES: int = 60

    # Turn off to let accounts log in immediately without verifying.
    REQUIRE_EMAIL_VERIFICATION: bool = True

    # Where the verification link points. Must be the frontend, not the API.
    FRONTEND_URL: str = "http://localhost:3000"

    # When SMTP_HOST is empty the mailer prints the message (and the
    # verification link) to the backend console instead of sending it.
    # That keeps the whole flow testable with no mail account.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "Project Atlas <no-reply@localhost>"
    SMTP_STARTTLS: bool = True

    SESSION_COOKIE_NAME: str = "atlas_token"
    # Must stay False on plain-HTTP localhost or the browser silently drops
    # the cookie. Set true in any deployed environment.
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"


settings = Settings()