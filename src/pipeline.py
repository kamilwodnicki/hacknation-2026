"""The whole processing chain for one PDF, shared by the CLI, the API and the UI:

    PDF -> ingestion (text layer / OCR) -> classification -> extraction -> result

The result holds the output JSON in the exact UZP format (`output`, empty dict for an
unrecognized document) and the metadata explaining how it was obtained.
"""

import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.classification import ClassificationResult, classify
from src.config import Settings, get_settings
from src.extraction import DocumentType, FieldTrace, extract, load_document_types
from src.ingestion import IngestedDocument, IngestionError, read_pdf
from src.llm import LLMError, get_llm_client
from src.llm.cache import CachedLLM
from src.llm.extractor import empty_result, has_gaps, llm_extract, merge

log = logging.getLogger(__name__)

# OCR and ONNX Runtime already use all CPU cores; processing documents one at a time
# keeps memory predictable on a 16 GB laptop and avoids sharing the OCR engine.
_processing_lock = threading.Lock()


class IngestionInfo(BaseModel):
    page_count: int
    ocr_pages: list[int]
    skipped_pages: list[int]


class LLMInfo(BaseModel):
    """How the language model was used for this document (transparency)."""

    mode: str
    used: bool = False
    model: str | None = None
    cached: bool = False
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None
    skipped_reason: str | None = None


class PipelineResult(BaseModel):
    filename: str
    document_type: str | None
    """None = not recognized (or unreadable) -> empty output JSON."""
    output: dict[str, Any]
    """JSON in the UZP format, written to output/<name>.json."""
    classification: ClassificationResult | None = None
    fields: dict[str, FieldTrace] = {}
    ingestion: IngestionInfo | None = None
    llm: LLMInfo | None = None
    error: str | None = None
    seconds: float = 0.0
    pages_text: list[str] | None = None
    """Extracted text per page (only when requested, e.g. for the UI preview)."""


@lru_cache
def _cached_types(config_dir: str) -> dict[str, DocumentType]:
    return load_document_types(Path(config_dir) / "document_types")


def document_types(settings: Settings | None = None) -> dict[str, DocumentType]:
    """Document types from config/document_types (loaded and validated once)."""
    s = settings or get_settings()
    return _cached_types(str(s.config_dir))


_llm_client: Any = None
_llm_client_error: str | None = None
_llm_lock = threading.Lock()


def llm_client(settings: Settings | None = None) -> Any:
    """The configured, cached LLM client or None (rules only). Created once per process."""
    global _llm_client, _llm_client_error
    s = settings or get_settings()
    with _llm_lock:
        if _llm_client is None and _llm_client_error is None:
            try:
                client = get_llm_client(s)
                _llm_client = CachedLLM(client, s.llm_cache_dir) if client else False
            except LLMError as exc:
                _llm_client_error = str(exc)
                log.warning("LLM wyłączony: %s", exc)
                _llm_client = False
    return _llm_client or None


def effective_mode(settings: Settings) -> str:
    return settings.extraction_mode if llm_client(settings) else "rules"


def extract_with_llm(
    doc: IngestedDocument, doc_type: DocumentType, settings: Settings | None = None, mode: str | None = None
) -> tuple[Any, LLMInfo]:
    """Rules, then (depending on the mode) the language model, merged field by field."""
    s = settings or get_settings()
    mode = mode or effective_mode(s)
    info = LLMInfo(mode=mode)
    if mode != "rules" and not llm_client(s):
        info.mode, info.error = "rules", _llm_client_error or "LLM nie jest skonfigurowany"

    rules = extract(doc, doc_type)
    if info.mode == "rules":
        return rules, info
    if info.mode == "hybrid" and not has_gaps(rules, doc_type):
        info.skipped_reason = "reguły wypełniły wszystkie pola"
        return rules, info

    base = rules if info.mode == "hybrid" else empty_result(doc_type)
    try:
        llm_data, response = llm_extract(doc, doc_type, llm_client(s), s.llm_max_chars, s.llm_max_output_tokens)
    except LLMError as exc:
        info.error = str(exc)
        log.warning("%s: LLM nie zadziałał (%s)", doc.filename, exc)
        return base, info
    info.used, info.model, info.cached = True, response.model, response.cached
    info.input_tokens, info.output_tokens = response.input_tokens, response.output_tokens
    return merge(base, llm_data, doc, doc_type, response.model, arbiter=llm_client(s)), info


def process_ingested(
    doc: IngestedDocument, types: dict[str, DocumentType], settings: Settings | None = None, mode: str | None = None
) -> tuple[ClassificationResult, Any, LLMInfo]:
    s = settings or get_settings()
    classification = classify(doc, types)
    if classification.document_type is None:
        return classification, None, LLMInfo(mode=mode or effective_mode(s))
    extraction, info = extract_with_llm(doc, types[classification.document_type], s, mode)
    return classification, extraction, info


def process_pdf(
    source: str | Path | bytes,
    filename: str | None = None,
    settings: Settings | None = None,
    include_text: bool = False,
) -> PipelineResult:
    s = settings or get_settings()
    name = filename or (Path(source).name if isinstance(source, (str, Path)) else "document.pdf")
    start = time.perf_counter()
    with _processing_lock:
        try:
            doc = read_pdf(source, filename=name, settings=s)
        except IngestionError as exc:
            log.warning("%s", exc)
            return PipelineResult(
                filename=name, document_type=None, output={}, error=str(exc), seconds=time.perf_counter() - start
            )
        classification, extraction, llm_info = process_ingested(doc, document_types(s), s)

    return PipelineResult(
        filename=name,
        document_type=classification.document_type,
        output=extraction.data if extraction else {},
        classification=classification,
        fields=extraction.fields if extraction else {},
        ingestion=IngestionInfo(page_count=doc.page_count, ocr_pages=doc.ocr_pages, skipped_pages=doc.skipped_pages),
        llm=llm_info,
        seconds=round(time.perf_counter() - start, 2),
        pages_text=[p.text for p in doc.pages] if include_text else None,
    )
