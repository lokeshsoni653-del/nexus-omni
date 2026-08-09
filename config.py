import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # ── Application ─────────────────────────────────────────────────────
    APP_NAME: str = "OmniMind AI"
    APP_VERSION: str = "0.5.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(default="omnimind-dev-secret-key-change-in-production")
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key-omnimind-production-grade")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite:///./omnimind.db",
        description="SQLAlchemy database URL"
    )
    DATABASE_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # ── Celery ───────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = Field(default="")
    CELERY_RESULT_BACKEND: str = Field(default="")
    CELERY_TASK_ALWAYS_EAGER: bool = Field(
        default=True,
        description="Run Celery tasks synchronously in dev mode"
    )

    # ── File Upload & Cloud Storage ──────────────────────────────────────
    UPLOAD_DIR: str = Field(default="./uploads")
    MAX_UPLOAD_SIZE_MB: int = 50

    # AWS S3 / Supabase Storage Configuration
    USE_S3_STORAGE: bool = Field(default=False)
    S3_BUCKET_NAME: str = Field(default="omnimind-storage")
    S3_ENDPOINT_URL: str = Field(default="")  # Custom endpoint for Supabase/MinIO
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_REGION: str = Field(default="us-east-1")

    # ── ChromaDB ─────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = Field(default="./chroma_db")
    CHROMA_COLLECTION_NAME: str = "omnimind_pdf_knowledge"

    # ── Agent Settings ───────────────────────────────────────────────────
    OPENAI_API_KEY: str = Field(default="")

    def model_post_init(self, __context):
        if not self.CELERY_BROKER_URL:
            object.__setattr__(self, "CELERY_BROKER_URL", self.REDIS_URL)
        if not self.CELERY_RESULT_BACKEND:
            object.__setattr__(self, "CELERY_RESULT_BACKEND", self.REDIS_URL)
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
