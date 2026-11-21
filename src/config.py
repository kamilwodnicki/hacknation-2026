"""Application settings read from environment variables and ONE settings file:

* `.env.overdrive` when it exists — then `.env` is ignored completely,
* otherwise `.env`.

Files are looked up in PISMO_ENV_DIR (the project folder mounted read-only in Docker) or the
current directory. Explicit environment variables always win over the file.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

OVERDRIVE_FILE = ".env.overdrive"
DEFAULT_FILE = ".env"


def settings_file() -> Path:
    """The settings file in use: .env.overdrive if present, else .env (may not exist)."""
    directory = Path(os.getenv("PISMO_ENV_DIR", "."))
    overdrive = directory / OVERDRIVE_FILE
    return overdrive if overdrive.is_file() else directory / DEFAULT_FILE


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # LLM — which provider to use: openai (any OpenAI-compatible API — by default Mistral AI,
    # EU endpoint), vertex (Google Cloud), none (rules only). Without a key the application
    # falls back to rules and says so.
    llm_provider: Literal["none", "vertex", "openai"] = "openai"
    llm_timeout: float = 120.0
    extraction_mode: Literal["rules", "llm", "hybrid"] = "hybrid"
    """rules = YAML rules only; llm = the model fills the whole JSON; hybrid = rules first,
    the model fills what the rules left empty (per-field policy `llm:` in YAML).
    Without a configured provider every mode falls back to rules."""
    llm_max_chars: int = 40000
    """Document text sent to the model is cut to this many characters (~11k tokens)."""
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

    # OpenAI-compatible API — defaults: Mistral AI EU endpoint, Ministral 3 14B (Apache 2.0)
    llm_api_base_url: str | None = "https://api.eu.mistral.ai/v1"
    llm_api_key: str | None = None
    llm_model_name: str | None = "ministral-14b-2512"

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
    ocr_max_pages: int = 2
    """Maximum number of scanned pages OCR-ed per document (0 = no limit). The data of every
    document type is on the first pages (appeal: header + first charge on pages 1-2; the
    justification follows), so 2 pages give the same result as the whole document at a
    fraction of the time. Pages with a text layer are always read in full."""
    ocr_det_model: Literal["tiny", "small"] = "tiny"
    """Text detection model (PP-OCRv6): tiny ~3x faster than small, same recognition."""
    ocr_det_model_path: Path | None = Path("models/ocr/PP-OCRv6_det_tiny.onnx")
    """Bundled tiny model (no download at runtime); used when ocr_det_model = tiny."""
    ocr_engine: Literal["openvino", "onnxruntime"] = "openvino"
    """Inference engine: OpenVINO is ~30% faster on CPU with identical text; when it cannot be
    loaded, ONNX Runtime is used automatically."""
    ocr_use_cls: bool = False
    """Text-line orientation classifier (only needed for upside-down text lines)."""
    ocr_cache_dir: Path | None = Path("cache/ocr")
    """OCR results cached by file content + page + DPI + model (empty = no cache)."""

    # Batch processing
    workers: int = 4
    """Documents processed at the same time by the CLI: OCR (CPU) of one document overlaps
    with the LLM calls (network) of others. OCR itself runs one page at a time."""


@lru_cache
def get_settings() -> Settings:
    path = settings_file()
    return Settings(_env_file=path if path.is_file() else None, _env_file_encoding="utf-8")
