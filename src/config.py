"""Application settings read from environment variables / .env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (OpenAI-compatible API)
    llm_api_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model_name: str | None = None

    # Paths
    input_dir: Path = Path("input")
    output_dir: Path = Path("output")
    config_dir: Path = Path("config")

    # Ingestion / OCR
    ocr_dpi: int = 200
    """Rendering resolution for scanned pages sent to OCR."""
    ocr_min_text_chars: int = 30
    """A page with fewer alphanumeric characters in its text layer is treated as a scan."""
    ocr_max_pages: int = 0
    """Maximum number of pages OCR-ed per document (0 = no limit)."""


@lru_cache
def get_settings() -> Settings:
    return Settings()
