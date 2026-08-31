"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the OCR extraction service."""

    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
    groq_timeout_seconds: float = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
