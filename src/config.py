"""Application settings read from environment variables / .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM — which provider to use: none (rules only), vertex (Google Cloud), openai (any
    # OpenAI-compatible API, e.g. OVHcloud / Scaleway / Mistral EU endpoint).
    llm_provider: Literal["none", "vertex", "openai"] = "none"
    llm_timeout: float = 120.0
    extraction_mode: Literal["rules", "llm", "hybrid"] = "hybrid"
    """rules = YAML rules only; llm = the model fills the whole JSON; hybrid = rules first,
    the model fills what the rules left empty (per-field policy `llm:` in YAML).
    Without a configured provider every mode falls back to rules."""
    llm_max_chars: int = 30000
    """Document text sent to the model is cut to this many characters (~8.5k tokens)."""
    llm_max_output_tokens: int = 2000
    llm_cache_dir: Path = Path("cache/llm")
    """On-disk response cache: the same prompt is never paid for twice."""

    # Google Cloud Vertex AI (Gemini Enterprise Agent Platform), partner model Mistral.
    google_application_credentials: Path = Path("secrets/vertex-sa.json")
    """Service-account key file. Never committed (secrets/ is git- and docker-ignored)."""
    vertex_project: str | None = None
    """Project ID; when empty it is read from the service-account file."""
    vertex_region: str = "europe-west4"
    """europe-west4 = Netherlands; ML processing guaranteed within the EU for Mistral."""
    vertex_publisher: str = "mistralai"
    vertex_model: str = "mistral-small-2503"

    # OpenAI-compatible API (alternative provider)
    llm_api_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model_name: str | None = None

    # Paths
    input_dir: Path = Path("input")
    output_dir: Path = Path("output")
    config_dir: Path = Path("config")
    meta_dir: Path = Path("meta")
    """Extraction metadata (classification, per-field provenance), kept out of `output`
    so the output tree contains only the UZP JSON files."""
    write_meta: bool = True

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
